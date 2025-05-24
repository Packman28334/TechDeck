import socket

class MixerSubsystem:
    def __init__(self, ip_address: str):
        self.ip_address: str = ip_address
        
        self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.socket.connect((self.ip_address, 49280))

    def get_configuration(self) -> dict:
        return {
            "ip_address": self.ip_address
        }

    def enter_blackout(self):
        # Uses Mute Group 3 to Disable all Wanted Mics (The Blackout Mute Group)
        # We could set in setting what Mute Group is Blackout
        message = ("set MIXER:Current/MuteMaster/On 2 0 1 \n").encode() # Mute Group 3 ON
        self.socket.sendall(message)

    def exit_blackout(self):
        # Undoes enter_blackout
        message = ("set MIXER:Current/MuteMaster/On 2 0 0 \n").encode() # Mute Group 3 OFF
        self.socket.sendall(message)

    def send_requests(self, requests: list[str]):
        self.socket.sendall(("\n ".join(requests)+"\n").encode())
        #self.socket.recv(1500).decode()

    def identify_channel(self, channel: str) -> tuple[str, int]: # type, number
        channel = str(channel) # just in case
        if channel.startswith("ST"): # ST = Stereo
            return "StInCh/Fader", int(channel.removeprefix("ST"))
        elif channel.startswith("DCA"): # DCA = Groups
            return "DCA/Fader", int(channel.removeprefix("DCA"))
        elif channel.startswith("MIX"): # MTRX = Matrix
            return "Mix/Fader", int(channel.removeprefix("MIX"))
        elif channel.startswith("MTRX"): # MTRX = Matrix
            return "Mtrx/Fader", int(channel.removeprefix("MTRX"))
        elif channel.startswith("MUTE"): # MUTE = Mute Groups
            return "MuteMaster", int(channel.removeprefix("MUTE"))
        else:
            return "InCh/Fader", int(channel) # InCh = Input Channel

    def run_command(self, command: dict):
        match command["action"]:
            case "enable_channels": # Turns on any Input/Output Channel 
                commands = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/On {channel_number} 0 1")
                self.send_requests(commands)

            case "disable_channels": # Turns off any Input/Output Channel 
                commands = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/On {channel_number} 0 0")
                self.send_requests(commands)
            case "set_faders_on_channels":
                commands = []
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -inf, 5: -5, 8: 0, 17: -138} - provide a value in decibels from -138 to 10, or -inf
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/Level {channel_number} 0 {-32768 if value == '-inf' else value*100}")
                self.send_requests(commands)
                
            case "change_scene": # Change used scene
                # do we want scene value to been in channel or do we want to store it somewhre else?
                pass #Todo
            


# For Testing
if __name__ == "__main__":
    TestCommands: list[dict] = [
        {"subsystem": "mixer", "action": "enable_channels", "channels": {"DCA0", "ST1", "8", "MIX0"}},
        {"subsystem": "mixer", "action": "disable_channels", "channels": {"DCA0", "ST1", "8", "MIX0"}},
        {"subsystem": "mixer", "action": "set_faders_on_channels", "channels": {"DCA0":10, "ST1":-5, "8":"-inf"}},
        {"subsystem": "mixer", "action": "enable_channels", "channels": {"MUTE0"}},
        {"subsystem": "mixer", "action": "disable_channels", "channels": {"MUTE0"}}
    ]

    Mixer = MixerSubsystem("127.0.0.1")
    for i, Cue in enumerate(TestCommands, start=1):
        input(f"Run Cue {i}: ")
        Mixer.run_command(Cue)
