
from subsystems import MixerSubsystem, LightingSubsystem, SpotlightSubsystem, AudioSubsystem, BackgroundsSubsystem

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, commands: list[dict]):
        self.commands: list[dict] = commands

    def call(self, show: "Show", mixer_subsystem: MixerSubsystem, lighting_subsystem: LightingSubsystem, spotlight_subsystem: SpotlightSubsystem, audio_subsystem: AudioSubsystem, backgrounds_subsystem: BackgroundsSubsystem):
        for command in self.commands:
            #match command["type"]
            pass

class BlackoutCue(Cue):
    def __init__(self):
        super().__init__([])
    
    def call(self, show: "Show", mixer_subsystem: MixerSubsystem, lighting_subsystem: LightingSubsystem, spotlight_subsystem: SpotlightSubsystem, audio_subsystem: AudioSubsystem, backgrounds_subsystem: BackgroundsSubsystem):
        show.enter_blackout()