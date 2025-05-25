
from subsystems import MixerSubsystem, LightingSubsystem, SpotlightSubsystem, AudioSubsystem, BackgroundsSubsystem

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, description: str, commands: list[dict], blackout: bool = False):
        self.description: str = description
        self.commands: list[dict] = commands
        self.blackout: bool = blackout

    def call(self, mixer_subsystem: MixerSubsystem, lighting_subsystem: LightingSubsystem, spotlight_subsystem: SpotlightSubsystem, audio_subsystem: AudioSubsystem, backgrounds_subsystem: BackgroundsSubsystem):
        for command in self.commands:
            match command["subsystem"]:
                case "mixer":
                    mixer_subsystem.run_command(command)
                case "lighting":
                    lighting_subsystem.run_command(command)
                case "spotlight":
                    spotlight_subsystem.run_command(command)
                case "audio":
                    audio_subsystem.run_command(command)
                case "backgrounds":
                    backgrounds_subsystem.run_command(command)
                case other:
                    print(f"Unknown subsystem {other} in command")