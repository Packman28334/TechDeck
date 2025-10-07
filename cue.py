
from pydantic import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, description: str, commands: list[dict], notes: str = "", blackout: bool = False):
        self.description: str = description
        self.notes: str = notes
        self.commands: list[dict] = commands
        self.blackout: bool = blackout
        self.show: "Show" | None = None

    @classmethod
    def deserialize(cls, serialized: dict):
        return cls(
            serialized["description"],
            serialized["commands"],
            notes=serialized["notes"],
            blackout=serialized["blackout"]
        )

    def serialize(self) -> dict:
        return {
            "description": self.description,
            "commands": self.commands,
            "notes": self.notes,
            "blackout": self.blackout
        }

    def call(self):
        if not self.show:
            return

        if self.blackout:
            self.show.enter_blackout() # if the blackout flag is set, we want to enter blackout
        else:
            self.show.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it
        
        for command in self.commands:
            match command["subsystem"]:
                case "mixer":
                    self.show.mixer_subsystem.run_command(command)
                case "lights":
                    self.show.lighting_subsystem.run_command(command)
                case "spotlight":
                    self.show.spotlight_subsystem.run_command(command)
                case "audio":
                    self.show.audio_subsystem.run_command(command)
                case "backgrounds":
                    self.show.backgrounds_subsystem.run_command(command)
                case other:
                    print(f"Unknown subsystem {other} in command")

    def _cue_changed(self):
        if self.show:
            if self.show.p2p_network_manager.is_master_node:
                self.show.p2p_network_manager.broadcast_to_servers("cue_edited", {"index": self.show.cue_list.index(self), "cue": self.serialize()})
            self.show.save(self.show.title)

    def append_command(self, command: dict):
        self.commands.append(command)
        self._cue_changed()
    
    def insert_command(self, position: int, command: dict):
        self.commands.insert(position, command)
        self._cue_changed()

    def pop_command(self, position: int) -> dict:
        command: dict = self.commands.pop(position)
        self._cue_changed()
        return command

    def move_command(self, old_position: int, new_position: int):
        if new_position > old_position:
            self.commands.insert(new_position-1, self.commands.pop(old_position))
        elif new_position < old_position:
            self.commands.insert(new_position+1, self.commands.pop(old_position))
        self._cue_changed()

    def update_command(self, position: int, partial_command: dict) -> dict:
        for k, v in partial_command.items():
            self.commands[position][k] = v
        self._cue_changed()
        return self.commands[position]

    def __str__(self) -> str:
        if self.blackout:
            return f"Blackout cue \"{self.description}\""
        else:
            return f"Cue \"{self.description}\""

class CueModel(BaseModel):
    description: str
    notes: str
    commands: list[dict] = []
    blackout: bool = False

class PartialCueModel(BaseModel):
    description: str | None = None
    notes: str | None = None
    commands: list[dict] | None = None
    blackout: bool | None = None