
from cue import Cue, BlackoutCue
from subsystems import MixerSubsystem, LightingSubsystem, SpotlightSubsystem, AudioSubsystem, BackgroundsSubsystem

DEFAULT_CONFIGURATION = {
    "mixer_subsystem": {
        "ip_address": "10.72.2.100"
    },
    "lighting_subsystem": {
        "ip_address": "10.72.2.101",
        "port_tx": 8000
    },
    "spotlight_subsystem": {},
    "audio_subsystem": {},
    "backgrounds_subsystem": {}
}

class Show:
    def __init__(self, title: str, cues: list[Cue | BlackoutCue], configuration: dict):
        self.title: str = title

        self.cues: list[Cue | BlackoutCue] = cues
        self.current_cue: int = -1

        self.blackout: bool = False

        self.mixer_subsystem: MixerSubsystem = MixerSubsystem(**configuration["mixer_subsystem"])
        self.lighting_subsystem: LightingSubsystem = LightingSubsystem(**configuration["lighting_subsystem"])
        self.spotlight_subsystem: SpotlightSubsystem = SpotlightSubsystem(**configuration["spotlight_subsystem"])
        self.audio_subsystem: AudioSubsystem = AudioSubsystem(**configuration["audio_subsystem"])
        self.backgrounds_subsystem: BackgroundsSubsystem = BackgroundsSubsystem(**configuration["backgrounds_subsystem"])

    @classmethod
    def new(cls, title: str, configuration: dict | None):
        return cls(title, [], configuration if configuration else DEFAULT_CONFIGURATION)
    
    @classmethod
    def load(cls, filename: str):
        pass

    def save(self, filename: str):
        pass

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
        self.exit_blackout()
        self.current_cue += 1
        self.cues[self.current_cue].call(self, self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)

    def previous_cue(self):
        self.exit_blackout()
        if self.current_cue < 1:
            return
        self.current_cue -= 1
        self.cues[self.current_cue].call(self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)

    def jump_to_cue(self, index: int):
        self.exit_blackout()
        self.current_cue = index
        self.cues[self.current_cue].call(self.mixer_subsystem, self.lighting_subsystem, self.spotlight_subsystem, self.audio_subsystem, self.backgrounds_subsystem)