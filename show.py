
import zipfile, shutil, pathlib, json, os

from cue_list import CueList
from subsystems import MixerSubsystem, LightingSubsystem, SpotlightSubsystem, AudioSubsystem, ScenerySubsystem
from p2p_networking import p2p_network_manager, P2PNetworkManager
from config import DEBUG_MODE

DEFAULT_CONFIGURATION = {
    "mixer_subsystem": {
        "blackout_mute_group": 1,
        "aliases": {
            "WL": [13, 14],
            "HANG": [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }
    },
    "lighting_subsystem": {
        "initial_playback": 1
    },
    "spotlight_subsystem": {},
    "audio_subsystem": {},
    "scenery_subsystem": {}
}

if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
    shutil.rmtree("_working_show")
os.mkdir("_working_show")
os.mkdir("_working_show/backdrop_library") # this must exist for the StaticFiles to be mounted

class Show:
    def __init__(self, title: str, cue_list: CueList, configuration: dict):
        self.title: str = title

        self.p2p_network_manager: P2PNetworkManager = p2p_network_manager

        self.cue_list: CueList = cue_list
        self.cue_list.set_show(self)
        self.current_cue: int = -1

        self.blackout: bool = False

        self.mixer_subsystem: MixerSubsystem = MixerSubsystem(**configuration["mixer_subsystem"])
        self.lighting_subsystem: LightingSubsystem = LightingSubsystem(**configuration["lighting_subsystem"])
        self.spotlight_subsystem: SpotlightSubsystem = SpotlightSubsystem(self.p2p_network_manager, **configuration["spotlight_subsystem"])
        self.audio_subsystem: AudioSubsystem = AudioSubsystem(**configuration["audio_subsystem"])
        self.scenery_subsystem: ScenerySubsystem = ScenerySubsystem(self.p2p_network_manager, **configuration["scenery_subsystem"])

    @classmethod
    def new(cls, title: str):
        obj = cls(title, CueList(), DEFAULT_CONFIGURATION)
        if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
            shutil.rmtree("_working_show/")
        os.mkdir("_working_show")
        os.mkdir("_working_show/audio_library")
        os.mkdir("_working_show/backdrop_library")
        pathlib.Path("_working_show/cue_list.json").write_text('{"cues": []}')
        pathlib.Path("_working_show/configuration.json").write_text(json.dumps(DEFAULT_CONFIGURATION))
        obj.save(title)
        return obj
    
    @classmethod
    def load(cls, filename: str):
        if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
            shutil.rmtree("_working_show/")
        with zipfile.ZipFile(f"shows/{filename}.tdshw", "r") as zip:
            zip.extractall("_working_show/")
        return cls(
            filename,
            CueList.create_from_serialized(json.loads(pathlib.Path("_working_show/cue_list.json").read_text())["cues"]),
            json.loads(pathlib.Path("_working_show/configuration.json").read_text()),
        )

    @classmethod
    def load_or_create(cls, title: str):
        if os.path.exists(f"shows/{title}.tdshw"):
            return cls.load(title)
        else:
            return cls.new(title)

    def accumulate_subsystem_configuration(self) -> dict:
        return {
            "mixer_subsystem": self.mixer_subsystem.get_configuration(),
            "lighting_subsystem": self.lighting_subsystem.get_configuration(),
            "spotlight_subsystem": self.spotlight_subsystem.get_configuration(),
            "audio_subsystem": self.audio_subsystem.get_configuration(),
            "scenery_subsystem": self.scenery_subsystem.get_configuration()
        }

    def accumulate_subsystem_states(self) -> dict:
        return {
            "mixer_subsystem": self.mixer_subsystem.state,
            "lighting_subsystem": self.lighting_subsystem.state,
            "spotlight_subsystem": self.spotlight_subsystem.state,
            "audio_subsystem": self.audio_subsystem.state,
            "scenery_subsystem": self.scenery_subsystem.state
        }
    
    def update_subsystem_states(self, states: dict):
        self.mixer_subsystem.state = states["mixer_subsystem"]
        self.lighting_subsystem.state = states["lighting_subsystem"]
        self.spotlight_subsystem.state = states["spotlight_subsystem"]
        self.audio_subsystem.state = states["audio_subsystem"]
        self.scenery_subsystem.state = states["scenery_subsystem"]

    def save(self, filename: str, backup: bool = False):
        if not os.path.exists("_working_show/"):
            return
        if not os.path.exists("shows/"):
            os.mkdir("shows")
        full_filename: str = f"shows/{filename}.tdshw"
        if backup:
            full_filename += ".bak"
        if os.path.exists(full_filename):
            os.remove(full_filename)
        pathlib.Path("_working_show/cue_list.json").write_text(json.dumps({"cues": self.cue_list.serialize()}))
        pathlib.Path("_working_show/configuration.json").write_text(json.dumps(self.accumulate_subsystem_configuration()))
        shutil.make_archive(f"shows/{filename}", "zip", "_working_show/")
        os.rename(f"shows/{filename}.zip", full_filename)
        self.p2p_network_manager.broadcast_to_servers("save_state_changed", False)
        self.p2p_network_manager.broadcast_to_client("save_state_changed", False)
        self.cue_list.unsaved = False

    @staticmethod
    def list_shows() -> list[str]:
        if not os.path.exists("shows/"):
            os.mkdir("shows")
        return [show_name.removesuffix(".tdshw") for show_name in os.listdir("shows") if show_name.endswith(".tdshw")]

    def enter_blackout(self):
        if not self.p2p_network_manager.is_master_node:
            return
        if self.blackout:
            return False
        self.mixer_subsystem.enter_blackout()
        self.lighting_subsystem.enter_blackout()
        self.spotlight_subsystem.enter_blackout()
        self.scenery_subsystem.enter_blackout()
        self.blackout = True
        self.p2p_network_manager.broadcast_to_servers("blackout_state_changed", {"new_state": True})
        self.p2p_network_manager.broadcast_to_client("blackout_state_changed", {"new_state": True})
        if DEBUG_MODE:
            print("Entered blackout")
        return True
    
    def exit_blackout(self):
        if not self.p2p_network_manager.is_master_node:
            return
        if not self.blackout:
            return False
        self.mixer_subsystem.exit_blackout()
        self.lighting_subsystem.exit_blackout()
        self.spotlight_subsystem.exit_blackout()
        self.scenery_subsystem.exit_blackout()
        self.blackout = False
        self.p2p_network_manager.broadcast_to_servers("blackout_state_changed", {"new_state": False})
        self.p2p_network_manager.broadcast_to_client("blackout_state_changed", {"new_state": False})
        if DEBUG_MODE:
            print("Exited blackout")
        return True

    def trigger_cue(self):
        self.cue_list[self.current_cue].call()
        self.p2p_network_manager.broadcast_to_servers("subsystem_state_changed", self.accumulate_subsystem_states())
        self.p2p_network_manager.broadcast_to_servers("current_cue_changed", {"index": self.current_cue})
        self.p2p_network_manager.broadcast_to_client("current_cue_changed", {"index": self.current_cue})

    def next_cue(self):
        if not self.p2p_network_manager.is_master_node:
            return
        self.current_cue += 1
        if self.current_cue > len(self.cue_list)-1:
            self.current_cue = 0
        self.trigger_cue()
        return self.current_cue

    def previous_cue(self):
        if not self.p2p_network_manager.is_master_node:
            return
        self.current_cue -= 1
        if self.current_cue < 0:
            self.current_cue = len(self.cue_list)-1
        self.trigger_cue()
        return self.current_cue

    def jump_to_cue(self, index: int):
        if not self.p2p_network_manager.is_master_node:
            return
        if index > len(self.cue_list)-1 or index < 0:
            return self.current_cue
        self.current_cue = index
        self.trigger_cue()
        return self.current_cue

    def update_polling_tasks(self):
        self.audio_subsystem.update_polling_tasks()
