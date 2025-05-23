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
        if channel.startswith("ST"):
            return "StInCh", int(channel.removeprefix("ST"))
        elif channel.startswith("DCA"):
            return "DCA", int(channel.removeprefix("DCA"))
        elif channel.startswith("MTRX"):
            return "Mtrx", int(channel.removeprefix("MTRX"))
        else:
            return "InCh", int(channel)

    def run_command(self, command: dict):
        match command["action"]:
            case "enable_channels": # Turns on any Input/Output Channel 
                commands = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 1")
                self.send_requests(commands)

            case "disable_channels":# Turns off any Input/Output Channel 
                commands = []
                for channel in command["channels"]:
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/Fader/On {channel_number} 0 0")
                self.send_requests(commands)

            case "set_faders_on_channels":
                commands = []
                for channel, value in command["channels"].items(): # ex. command["channels"] = {0: -inf, 5: -5, 8: 0, 17: -138} - provide a value in decibels from -138 to 10, or -inf
                    channel_type, channel_number = self.identify_channel(channel)
                    commands.append(f"set MIXER:Current/{channel_type}/Fader/Level {channel_number} 0 {-32768 if value == '-inf' else value*100}")
                self.send_requests(commands)