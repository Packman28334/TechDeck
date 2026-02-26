
from uuid import uuid4

from config import DEBUG_MODE

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from show import Show

class Cue:
    def __init__(self, description: str, commands: list[dict], notes: str = "", uuid: str = ""):
        self.description: str = description
        self.notes: str = notes
        self.commands: list[dict] = commands
        self.uuid: str = uuid if uuid else str(uuid4())
        self.show: "Show" | None = None

    @classmethod
    def deserialize(cls, serialized: dict):
        return cls(
            serialized["description"],
            serialized["commands"],
            notes=serialized["notes"],
            uuid=serialized["uuid"]
        )

    def serialize(self) -> dict:
        return {
            "description": self.description,
            "commands": self.commands,
            "notes": self.notes,
            "uuid": self.uuid
        }

    @classmethod
    def parse_from_spreadsheet(cls, row: list[str]):
        cue = cls(row[3], [], row[9])

        if not row[8].startswith("#CONT'D"): # if we don't explicity want to continue an audio file,
            cue.commands.append({"subsystem": "audio", "action": "stop", "fade_out": "1250"}) # we stop it.
        # the fade out takes 1.25s and is blocking, so we want to make sure we don't put it between stage lights and the backdrop, for example.
        # therefore we do it right now before anything else.

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

        if row[5].strip().startswith("PB#"):
            cue.commands.append({"subsystem": "lights", "action": "switch_playback", "playback": row[5].strip().split()[0].removeprefix("PB#")})
        elif row[5].strip().startswith("#BO"):
            cue.commands.append({"subsystem": "lights", "action": "jump_to_cue", "cue": "0.1"})
        elif row[5].strip().startswith("#"):
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

        if not row[8].startswith("#CONT'D"): # if we're not continuing a previous sound,
            if row[8].startswith("#"): # if we're requesting another sound,
                cue.commands.append({"subsystem": "audio", "action": "play", "index": row[8].strip().split()[0].removeprefix("#")}) # we play it.
            if row[8].startswith("L#"): # if we're requesting another sound but looping this time,
                cue.commands.append({"subsystem": "audio", "action": "play", "index": row[8].strip().split()[0].removeprefix("L#"), "loops": -1}) # we play it (but looping).

        for command in cue.commands: # add UUIDs for frontend manipulation
            command["id"] = str(uuid4())

        return cue

    def call(self):
        if not self.show:
            print("!!! CUE WITHOUT A SHOW REFERENCE")
            return
        
        if DEBUG_MODE:
            print(f"Cue \"{self.description}\" triggered ({self.uuid})")

        for command in self.commands:
            if DEBUG_MODE:
                print(f"Running command {command}")

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

        if DEBUG_MODE:
            print(f"Cue execution completed")

    def __str__(self) -> str:
        return f"Cue \"{self.description}\" ({self.uuid})"