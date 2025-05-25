
import zipfile, shutil, pathlib, json, os

from cue import Cue
from subsystems import MixerSubsystem, LightingSubsystem, SpotlightSubsystem, AudioSubsystem, BackgroundsSubsystem

DEFAULT_CONFIGURATION = {
    "mixer_subsystem": {
        "ip_address": "10.72.2.100"
    },
    "lighting_subsystem": {
        "ip_address": "10.72.2.101",
        "port_tx": 8000,
        "initial_playback": 1
    },
    "spotlight_subsystem": {},
    "audio_subsystem": {},
    "backgrounds_subsystem": {}
}

class Show:
    def __init__(self, title: str, cues: list[Cue], configuration: dict):
        self.title: str = title

        self.cues: list[Cue] = cues
        self.current_cue: int = -1

        self.blackout: bool = False

        self.mixer_subsystem: MixerSubsystem = MixerSubsystem(**configuration["mixer_subsystem"])
        self.lighting_subsystem: LightingSubsystem = LightingSubsystem(**configuration["lighting_subsystem"])
        self.spotlight_subsystem: SpotlightSubsystem = SpotlightSubsystem(**configuration["spotlight_subsystem"])
        self.audio_subsystem: AudioSubsystem = AudioSubsystem(**configuration["audio_subsystem"])
        self.backgrounds_subsystem: BackgroundsSubsystem = BackgroundsSubsystem(**configuration["backgrounds_subsystem"])

    @classmethod
    def new(cls, title: str, configuration: dict | None = None):
        return cls(title, [], configuration if configuration else DEFAULT_CONFIGURATION)
    
    @classmethod
    def load(cls, filename: str):
        if os.path.exists("_working_show/") and os.path.isdir("_working_show/"):
            shutil.rmtree("_working_show/")
        with zipfile.ZipFile(f"shows/{filename}.tdshw", "r") as zip:
            zip.extractall("_working_show/")
        return cls(
            filename,
            Show.deserialize_cues(json.loads(pathlib.Path("_working_show/cue_list.json").read_text())["cues"]),
            json.loads(pathlib.Path("_working_show/configuration.json").read_text()),
        )

    def accumulate_subsystem_configuration(self) -> dict:
        return {
            "mixer_subsystem": self.mixer_subsystem.get_configuration(),
            "lighting_subsystem": self.lighting_subsystem.get_configuration(),
            "spotlight_subsystem": self.spotlight_subsystem.get_configuration(),
            "audio_subsystem": self.audio_subsystem.get_configuration(),
            "backgrounds_subsystem": self.backgrounds_subsystem.get_configuration()
        }

    @staticmethod
    def deserialize_cues(cues: list[dict]) -> list[Cue]:
        out = []
        for cue in cues:
            out.append(Cue(
                cue["description"],
                cue["commands"],
                blackout=cue["blackout"]
            ))
        return out

    def serialize_cues(self) -> list[dict]:
        out: list[dict] = []
        for cue in self.cues:
            out.append({
                "description": cue.description,
                "commands": cue.commands,
                "blackout": cue.blackout
            })
        return out

    def save(self, filename: str):
        if not os.path.exists("shows/"):
            os.mkdir("shows")
        if os.path.exists(f"shows/{filename}.tdshw"):
            os.rmdir(f"shows/{filename}.tdshw")
        pathlib.Path("_working_show/cue_list.json").write_text(json.dumps({"cues": self.serialize_cues()}))
        pathlib.Path("_working_show/configuration.json").write_text(json.dumps(self.accumulate_subsystem_configuration()))
        with zipfile.ZipFile(f"shows/{filename}.tdshw", "w") as zip:
            files: dict[str, str] = {filename: os.path.join(directory_path, filename) for directory_path, subdirectories, filenames in os.walk("_working_show/") for filename in filenames} # https://stackoverflow.com/a/18394205
            for filename, file_path in files.items():
                zip.write(file_path, filename)

    def enter_blackout(self):
        if self.blackout:
            return
        self.mixer_subsystem.enter_blackout()
        self.lighting_subsystem.enter_blackout()
        self.spotlight_subsystem.enter_blackout()
        self.backgrounds_subsystem.enter_blackout()
        self.blackout = True
    
    def exit_blackout(self):
        if not self.blackout:
            return
        self.mixer_subsystem.exit_blackout()
        self.lighting_subsystem.exit_blackout()
        self.spotlight_subsystem.exit_blackout()
        self.backgrounds_subsystem.exit_blackout()
        self.blackout = False

    def next_cue(self):
        self.current_cue += 1
        if self.cues[self.current_cue].blackout:
            self.enter_blackout() # if the blackout flag is set on a cue, we want to enter blackout
        else:
            self.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it
        self.cues[self.current_cue].call(self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)

    def previous_cue(self):
        if self.current_cue < 1:
            return
        self.current_cue -= 1
        if self.cues[self.current_cue].blackout:
            self.enter_blackout() # if the blackout flag is set on a cue, we want to enter blackout
        else:
            self.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it
        self.cues[self.current_cue].call(self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)

    def jump_to_cue(self, index: int):
        self.current_cue = index
        if self.cues[self.current_cue].blackout:
            self.enter_blackout() # if the blackout flag is set on a cue, we want to enter blackout
        else:
            self.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it
        self.cues[self.current_cue].call(self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)