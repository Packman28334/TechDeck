
import zipfile, shutil, pathlib, json, os

from cue_list import CueList
from subsystems import MixerSubsystem, LightingSubsystem, AudioSubsystem, ScenerySubsystem
from p2p_networking import p2p_network_manager, P2PNetworkManager
from config import DEBUG_MODE

from typing import Callable

DEFAULT_CONFIGURATION: dict = {
    "mixer_subsystem": {
        "aliases": {
            "WL": [21],
            "HANG": [1, 2, 3, 4, 5, 6, 7, 8, 9]
        }
    },
    "lighting_subsystem": {
        "initial_playback": 1
    },
    "audio_subsystem": {},
    "scenery_subsystem": {}
}

if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
    shutil.rmtree("_working_show")
os.mkdir("_working_show")
os.mkdir("_working_show/audio_library") # this must exist for the StaticFiles to be mounted
os.mkdir("_working_show/backdrop_library") # ditto

class Show:
    def __init__(self, title: str, cue_list: CueList, configuration: dict):
        self.title: str = title

        self.p2p_network_manager: P2PNetworkManager = p2p_network_manager
        self.p2p_network_manager.show = self

        self.cue_list: CueList = cue_list
        self.cue_list.set_show(self)
        self.current_cue: int = -1
        self.staged_cue: int = -1
        self.cue_change_callbacks: list[Callable] = []

        self.mixer_subsystem: MixerSubsystem = MixerSubsystem(**configuration["mixer_subsystem"])
        self.lighting_subsystem: LightingSubsystem = LightingSubsystem(**configuration["lighting_subsystem"])
        self.audio_subsystem: AudioSubsystem = AudioSubsystem(**configuration["audio_subsystem"])
        self.scenery_subsystem: ScenerySubsystem = ScenerySubsystem(self.p2p_network_manager, **configuration["scenery_subsystem"])

    @classmethod
    def new(cls, title: str, configuration: dict = DEFAULT_CONFIGURATION):
        obj = cls(title, CueList(), configuration)
        if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
            shutil.rmtree("_working_show/")
        os.mkdir("_working_show")
        os.mkdir("_working_show/audio_library")
        os.mkdir("_working_show/backdrop_library")
        pathlib.Path("_working_show/cue_list.json").write_text('{"cues": []}')
        pathlib.Path("_working_show/configuration.json").write_text(json.dumps(configuration))
        obj.save(title)
        return obj
   
    @classmethod
    def load(cls, filename: str, override_configuration: dict | None = None):
        if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
            shutil.rmtree("_working_show/")
        with zipfile.ZipFile(f"shows/{filename}.tdshw", "r") as zip:
            zip.extractall("_working_show/")
        return cls(
            filename,
            CueList.create_from_serialized(json.loads(pathlib.Path("_working_show/cue_list.json").read_text())["cues"]),
            override_configuration if override_configuration else json.loads(pathlib.Path("_working_show/configuration.json").read_text()),
        )

    @classmethod
    def load_or_create(cls, title: str, override_configuration: dict | None = None):
        if os.path.exists(f"shows/{title}.tdshw"):
            return cls.load(title, override_configuration=override_configuration)
        else:
            return cls.new(title, configuration=override_configuration if override_configuration else DEFAULT_CONFIGURATION)

    def accumulate_subsystem_configuration(self) -> dict:
        return {
            "mixer_subsystem": self.mixer_subsystem.get_configuration(),
            "lighting_subsystem": self.lighting_subsystem.get_configuration(),
            "audio_subsystem": self.audio_subsystem.get_configuration(),
            "scenery_subsystem": self.scenery_subsystem.get_configuration()
        }

    def accumulate_subsystem_states(self) -> dict:
        return {
            "mixer_subsystem": self.mixer_subsystem.state,
            "lighting_subsystem": self.lighting_subsystem.state,
            "audio_subsystem": self.audio_subsystem.state,
            "scenery_subsystem": self.scenery_subsystem.state
        }
    
    def update_subsystem_states(self, states: dict):
        self.mixer_subsystem.state = states["mixer_subsystem"]
        self.lighting_subsystem.state = states["lighting_subsystem"]
        self.audio_subsystem.state = states["audio_subsystem"]
        self.scenery_subsystem.state = states["scenery_subsystem"]

    def save(self, filename: str, backup: bool = False):
        if DEBUG_MODE:
            print("Commencing save...")
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
        if DEBUG_MODE:
            print("Save completed.")

    @staticmethod
    def list_shows() -> list[str]:
        if not os.path.exists("shows/"):
            os.mkdir("shows")
        return [show_name.removesuffix(".tdshw") for show_name in os.listdir("shows") if show_name.endswith(".tdshw")]

    # TODO: re-add P2P

    def stage_next_cue(self) -> int:
        if self.staged_cue >= 0:
            self.staged_cue += 1
        else:
            self.staged_cue = self.current_cue + 1
        if self.staged_cue > len(self.cue_list)-1:
            self.staged_cue = 0
        for callback in self.cue_change_callbacks:
            callback()
        return self.staged_cue

    def stage_previous_cue(self) -> int:
        if self.staged_cue >= 0:
            self.staged_cue -= 1
        else:
            self.staged_cue = self.current_cue - 1
        if self.staged_cue < 0:
            self.staged_cue = len(self.cue_list)-1
        for callback in self.cue_change_callbacks:
            callback()
        return self.staged_cue

    def stage_cue(self, index: int) -> int:
        if index > len(self.cue_list)-1 or index < 0:
            return self.staged_cue
        self.staged_cue = index
        for callback in self.cue_change_callbacks:
            callback()
        return self.staged_cue

    def execute_staged_cue(self):
        if self.staged_cue < 0:
            self.stage_next_cue()
            return
        self.current_cue = self.staged_cue
        self.staged_cue = -1
        self.cue_list[self.current_cue].call()
        for callback in self.cue_change_callbacks:
            callback()

    def update_polling_tasks(self):
        self.audio_subsystem.update_polling_tasks()
