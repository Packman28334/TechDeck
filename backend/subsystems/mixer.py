import socket

class MixerSubsystem:
    def __init__(self, ip_address: str, dummy_mode: bool = False):
        self.ip_address: str = ip_address
        
        self.dummy_mode: bool = dummy_mode
        if not self.dummy_mode:
            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip_address, 49280))

    def get_configuration(self) -> dict:
        return {
            "ip_address": self.ip_address
        }

    def enter_blackout(self):
        if self.dummy_mode:
            return
        # Mutes group 1 (inputs)
        self.send_requests([f"set MIXER:Current/MuteMaster/On 0 0 1"])

    def exit_blackout(self):
        if self.dummy_mode:
            return
        # Unmutes group 1 (inputs)
        self.send_requests([f"set MIXER:Current/MuteMaster/On 0 0 0"])

    def send_requests(self, requests: list[str]):
        if self.dummy_mode:
            return
        self.socket.sendall(("\n ".join(requests)+"\n").encode())
        #self.socket.recv(1500).decode()

    def identify_channel(self, channel: str) -> tuple[str, int]: # type, number
        channel = str(channel) # just in case
        if channel.startswith("ST"): # ST = Stereo
            return "StInCh", int(channel.removeprefix("ST"))
        elif channel.startswith("DCA"): # DCA = Groups
            return "DCA", int(channel.removeprefix("DCA"))
        elif channel.startswith("MIX"): # MIX = Output
            return "Mix", int(channel.removeprefix("MIX"))
        elif channel.startswith("MTRX"): # MTRX = Matrix
            return "Mtrx", int(channel.removeprefix("MTRX"))
        else:
            return "InCh", int(channel)-1 # InCh = Input Channel

    def run_command(self, command: dict):
        if self.dummy_mode:
            return
        match command["action"]:
            case "enable_channels": # Turns on any Input/Output Channel 
                requests = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 1")
                self.send_requests(requests)

            case "disable_channels": # Turns off any Input/Output Channel 
                requests = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 0")
                self.send_requests(requests)

            case "set_faders_on_channels":
                requests = []
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -inf, 5: -5, 8: 0, 17: -138} - provide a value in decibels from -138 to 10, or -inf
                    channel_type, channel_number = self.identify_channel(channel)
                    requests.append(f"set MIXER:Current/{channel_type}/Fader/Level {channel_number} 0 {-32768 if value == '-inf' else value*100}")
                self.send_requests(requests)
                
            case "mute_group":
                self.send_requests([f"set MIXER:Current/MuteMaster/On {command['mute_group']+1} 0 1"])

            case "unmute_group":
                self.send_requests([f"set MIXER:Current/MuteMaster/On {command['mute_group']+1} 0 0"])

            case "change_scene": # Change used scene
                # do we want scene value to been in channel or do we want to store it somewhre else?
                pass #Todo
