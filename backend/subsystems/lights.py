
from pythonosc.udp_client import SimpleUDPClient

class LightingSubsystem:
    def __init__(self, ip_address: str, port_tx: int, initial_playback: int, dummy_mode: bool = False):
        self.ip_address: str = ip_address
        self.port_tx: int = port_tx
        self.initial_playback: int = initial_playback
        self.playback: int = initial_playback

        self.current_cue: float = 0.1

        self.dummy_mode: bool = dummy_mode
        if not dummy_mode:
            self.client: SimpleUDPClient = SimpleUDPClient(self.ip_address, self.port_tx)
            self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # ensure that initial cue of 0.1 is correct

    def get_configuration(self) -> dict:
        return {
            "ip_address": self.ip_address,
            "port_tx": self.port_tx,
            "initial_playback": self.initial_playback
        }

    def enter_blackout(self):
        if self.dummy_mode:
            return
        self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # jump to blackout cue (0.1)

    def exit_blackout(self): # doesn't seem to result in flash of incorrect lighting
        if self.dummy_mode:
            return
        self.client.send_message(f"/pb/{self.playback}/{self.current_cue}", 1.0) # jump to previous cue

    def run_command(self, command: dict):
        if self.dummy_mode:
            return
        match command["action"]:
            case "jump_to_cue":
                self.client.send_message(f"/pb/{self.playback}/{command['cue']}", 1.0)
                self.current_cue: float = command['cue']
            
            case "switch_playback":
                self.client.send_message(f"/pb/{self.playback}", 0.0)
                self.playback = command['playback']
                self.client.send_message(f"/pb/{self.playback}", 0.0 if "start_in_blackout" in command and command["start_in_blackout"] else 1.0)