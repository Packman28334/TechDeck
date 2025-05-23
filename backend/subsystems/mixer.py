
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
        command = ("set MIXER:Current/MuteMaster/On 2 0 1 \n").encode() # Mute Group 3 ON
        socket.sendall(command)

    def exit_blackout(self):
        # Undoes enter_blackout
        command = ("set MIXER:Current/MuteMaster/On 2 0 0 \n").encode() # Mute Group 3 OFF
        socket.sendall(command)

    def run_command(self, command: dict):
        match command["id"]:
            case "enable_channels":
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    pass #Todo
            case "disable_channels":
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    pass #Todo
            case "set_faders_on_channels":
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -32768, 5: -5000, 8: 0}
                    pass #Todo