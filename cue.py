
from pydantic import BaseModel
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, description: str, commands: list[dict], notes: str = "", blackout: bool = False, uuid: str = ""):
        self.description: str = description
        self.notes: str = notes
        self.commands: list[dict] = commands
        self.blackout: bool = blackout
        self.uuid: str = uuid if uuid else str(uuid4())
        self.show: "Show" | None = None

    @classmethod
    def deserialize(cls, serialized: dict):
        return cls(
            serialized["description"],
            serialized["commands"],
            notes=serialized["notes"],
            blackout=serialized["blackout"],
            uuid=serialized["uuid"]
        )

    def serialize(self) -> dict:
        return {
            "description": self.description,
            "commands": self.commands,
            "notes": self.notes,
            "blackout": self.blackout,
            "uuid": self.uuid
        }

    @classmethod
    def parse_from_spreadsheet(cls, row: list[str]):
        cue = cls(row[3], [], row[10], row[9] == "TRUE")

        enable_channels: list[str] = []
        for term in row[4].strip().split():
            if not term.startswith("-"):
                enable_channels.append(term)
        if enable_channels:
            cue.commands.append({"subsystem": "mixer", "action": "enable_channels", "channels": " ".join(enable_channels)})

        disable_channels: list[str] = []
        for term in row[4].strip().split():
            if term.startswith("-"):
                disable_channels.append(term.removeprefix("-"))
        if disable_channels:
            cue.commands.append({"subsystem": "mixer", "action": "disable_channels", "channels": " ".join(disable_channels)})

        if row[5].strip().startswith("#"):
            if row[5].startswith("#BO"):
                cue.commands.append({"subsystem": "lights", "action": "jump_to_cue", "cue": "0.1"})
            else:
                cue.commands.append({"subsystem": "lights", "action": "jump_to_cue", "cue": row[5].strip().split()[0].removeprefix("#")})

        if row[6].strip().startswith("#"):
            cue.commands.append({"subsystem": "spotlight", "action": "change_guide", "icon": row[6].strip().split()[0].removeprefix("#"), "guide": " ".join(row[6].strip().split()[1:])})
        elif row[6]:
            cue.commands.append({"subsystem": "spotlight", "action": "change_guide", "guide": row[6]})

        if row[7].startswith("#BO"):
            cue.commands.append({"subsystem": "scenery", "action": "enter_scenery_blackout"})
        elif row[7].startswith("V#"):
            cue.commands.append({"subsystem": "scenery", "action": "change_backdrop_to_video", "index": row[7].strip().split()[0].removeprefix("V#")})
        elif row[7].startswith("#"):
            cue.commands.append({"subsystem": "scenery", "action": "change_backdrop_to_image", "index": row[7].strip().split()[0].removeprefix("#")})

        if row[8].startswith("#"):
            cue.commands.append({"subsystem": "audio", "action": "play", "index": row[8].strip().split()[0].removeprefix("#")})

        return cue

    def call(self):
        if not self.show:
            return
        
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
                case "scenery":
                    self.show.scenery_subsystem.run_command(command)
                case other:
                    print(f"Unknown subsystem {other} in command")

        if self.blackout:
            self.show.enter_blackout() # if the blackout flag is set, we want to enter blackout
        else:
            self.show.exit_blackout() # if the blackout flag is not set, we want to exit blackout automatically if we're in it

    def __str__(self) -> str:
        if self.blackout:
            return f"Blackout cue \"{self.description}\" ({self.uuid})"
        else:
            return f"Cue \"{self.description}\" ({self.uuid})"