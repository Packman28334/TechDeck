import socket

from config import DUMMY_MODE, MIXER_IP

class MixerSubsystem:
    def __init__(self, blackout_mute_group: int, aliases: dict[str, list[str]]):
        self.blackout_mute_group: int = blackout_mute_group
        self.aliases: dict[str, list[str]] = {}
        
        if not DUMMY_MODE:
            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((MIXER_IP, 49280))

    def get_configuration(self) -> dict:
        return {
            "blackout_mute_group": self.blackout_mute_group,
            "aliases": self.aliases
        }

    @property
    def state(self) -> dict:
        return {}

    @state.setter
    def state(self, new_state: dict):
        pass

    def enter_blackout(self):
        if DUMMY_MODE:
            return
        self.send_requests([f"set MIXER:Current/MuteMaster/On {self.blackout_mute_group-1} 0 1"])

    def exit_blackout(self):
        if DUMMY_MODE:
            return
        self.send_requests([f"set MIXER:Current/MuteMaster/On {self.blackout_mute_group-1} 0 0"])

    def send_requests(self, requests: list[str]):
        if DUMMY_MODE:
            return
        self.socket.sendall(("\n ".join(requests)+"\n").encode())
        #self.socket.recv(1500).decode()

    def expand_aliases(self, channels: list[str]) -> list[str]:
        out: list[str] = []
        for channel in channels:
            if channel in self.aliases:
                out.extend(self.aliases[channel])
            else:
                out.append(channel)
        return out

    def identify_channel(self, channel: str) -> tuple[str, int]: # type, number
        channel = str(channel).upper() # just in case
        if channel.startswith("CH"): # CH = InCh = Input Channel
            return "InCh", int(channel.removeprefix("CH"))-1
        elif channel.startswith("STIN"): # STIN = Stereo In
            return "StInCh", int(channel.removeprefix("STIN"))
        elif channel.startswith("DCA"): # DCA = Groups
            return "DCA", int(channel.removeprefix("DCA"))
        elif channel.startswith("MIX"): # MIX = Output
            return "Mix", int(channel.removeprefix("MIX"))
        elif channel.startswith("MTRX"): # MTRX = Matrix
            return "Mtrx", int(channel.removeprefix("MTRX"))
        else:
            return "InCh", int(channel)-1 # InCh = Input Channel

    def run_command(self, command: dict):
        if DUMMY_MODE:
            return
        match command["action"]:
            case "enable_channels": # Turns on any Input/Output Channel 
                if isinstance(command["channels"], str):
                    channels: list = command["channels"].split(" ")
                else:
                    channels: list = command["channels"]
                requests = []
                for channel in channels:
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 1")
                self.send_requests(requests)

            case "disable_channels": # Turns off any Input/Output Channel 
                if isinstance(command["channels"], str):
                    channels: list = command["channels"].split(" ")
                else:
                    channels: list = command["channels"]
                requests = []
                for channel in channels:
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 0")
                self.send_requests(requests)

            case "set_faders_on_channels":
                if isinstance(command["channels"], str):
                    pairs: dict[str, float | str] = {}
                    for pair in command["channels"].split(" "):
                        value: float | str = pair.split("=")[1]
                        if value != "-inf":
                            value = float(value)
                        pairs[pair.split("=")[0]] = value
                else:
                    pairs: dict[str, float | str] = command["channels"]
                requests = []
                for channel, value in pairs.items(): # ex. command["channels"] = {0: -inf, 5: -5, 8: 0, 17: -138} - provide a value in decibels from -138 to 10, or -inf
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/Level {channel_number} 0 {-32768 if value == '-inf' else int(value*100)}")
                self.send_requests(requests)
                
            case "mute_group":
                self.send_requests([f"set MIXER:Current/MuteMaster/On {int(command['mute_group'])-1} 0 1"])

            case "unmute_group":
                self.send_requests([f"set MIXER:Current/MuteMaster/On {int(command['mute_group'])-1} 0 0"])

            case "change_scene":
                pass # TODO
