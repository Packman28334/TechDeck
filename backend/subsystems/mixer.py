
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
        pass

    def exit_blackout(self):
        pass

    def run_command(self, command: dict):
        match command["action"]:
            case "enable_channels":
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    pass # TODO
            case "disable_channels":
                for channel in command["channels"]: # ex. command["channels"] = [0, 5, 8]
                    pass # TODO
            case "set_faders_on_channels":
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -32768, 5: -5000, 8: 0}
                    pass # TODO