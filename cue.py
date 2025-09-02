
from pydantic import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, description: str, commands: list[dict], blackout: bool = False):
        self.description: str = description
        self.commands: list[dict] = commands
        self.blackout: bool = blackout

    def call(self, show: "Show"):
        if self.blackout:
            show.enter_blackout() # if the blackout flag is set, we want to enter blackout
        else:
            show.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it
        
        for command in self.commands:
            match command["subsystem"]:
                case "mixer":
                    show.mixer_subsystem.run_command(command)
                case "lighting":
                    show.lighting_subsystem.run_command(command)
                case "spotlight":
                    show.spotlight_subsystem.run_command(command)
                case "audio":
                    show.audio_subsystem.run_command(command)
                case "backgrounds":
                    show.backgrounds_subsystem.run_command(command)
                case other:
                    print(f"Unknown subsystem {other} in command")

    def append_command(self, command: dict):
        self.commands.append(command)
    
    def insert_command(self, position: int, command: dict):
        self.commands.insert(position, command)

    def pop_command(self, position: int) -> dict:
        return self.commands.pop(position)

    def move_command(self, old_position: int, new_position: int):
        if new_position > old_position:
            self.commands.insert(new_position-1, self.commands.pop(old_position))
        elif new_position < old_position:
            self.commands.insert(new_position+1, self.commands.pop(old_position))

    def update_command(self, position: int, partial_command: dict) -> dict:
        for k, v in partial_command.items():
            self.commands[position][k] = v
        return self.commands[position]

    def __str__(self) -> str:
        if self.blackout:
            return f"Blackout cue \"{self.description}\""
        else:
            return f"Cue \"{self.description}\""

class CueModel(BaseModel):
    description: str
    commands: list[dict] = []
    blackout: bool = False

class PartialCueModel(BaseModel):
    description: str | None = None
    commands: list[dict] | None = None
    blackout: bool | None = None