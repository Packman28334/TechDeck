
from pythonosc.udp_client import SimpleUDPClient

class LightingSubsystem:
    def __init__(self, ip_address: str, port_tx: int, initial_playback: int):
        self.ip_address: str = ip_address
        self.port_tx: int = port_tx
        self.initial_playback: int = initial_playback
        self.playback: int = initial_playback

        self.client: SimpleUDPClient = SimpleUDPClient(self.ip_address, self.port_tx)

    def get_configuration(self) -> dict:
        return {
            "ip_address": self.ip_address,
            "port_tx": self.port_tx,
            "initial_playback": self.initial_playback
        }

    def enter_blackout(self):
        pass

    def exit_blackout(self):
        pass

    def run_command(self, command: dict):
        match command["action"]:
            case "jump_to_cue":
                self.client.send_message(f"/pb/{self.playback}/{command['cue']}", 1.0)