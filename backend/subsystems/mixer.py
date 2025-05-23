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

    def run_command(self, command: dict):
        message = ""
        match command["action"]:
            case "enable_channels": # Turns on any Input/Output Channel 
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    message += f"set MIXER:Current/Channel/{command["fadertype"]}/On {channel} 0 1 \n "
                self.socket.sendall(message.encode())
            case "disable_channels":# Turns off any Input/Output Channel 
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    message += f"set MIXER:Current/Channel/{command["fadertype"]}/On {channel} 0 0 \n "
                self.socket.sendall(message.encode())
            case "set_faders_on_channels":
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -32768, 5: -5000, 8: 0}
                    pass #Todo
                
if __name__ == "__main__":
    TestCommands: list[dict] = [
        {"subsystem": "mixer", "action": "enable_channels", "fadertype": "InCh", "channels": [0, 5, 8]},
        {"subsystem": "mixer", "action": "enable_channels", "fadertype": "StInCh", "channels": [1]},
        {"subsystem": "mixer", "action": "disable_channels", "fadertype": "InCh", "channels": [0, 5, 8]},
        {"subsystem": "mixer", "action": "disable_channels", "fadertype": "StInCh", "channels": [1]}
    ]


    Mixer = MixerSubsystem("127.0.0.1")
    i: int = 1
    for Cue in TestCommands:
        input(f"Run Cue {i}: ")
        Mixer.run_command(Cue)
        i += 1
        