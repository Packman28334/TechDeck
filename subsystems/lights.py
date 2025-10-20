
from pythonosc.udp_client import SimpleUDPClient

from config import DUMMY_MODE, LIGHTING_IP, LIGHTING_PORT_TX

class LightingSubsystem:
    def __init__(self, initial_playback: int):
        self.initial_playback: int = initial_playback
        self.playback: int = initial_playback

        self.current_cue: float = 0.1

        if not DUMMY_MODE:
            self.client: SimpleUDPClient = SimpleUDPClient(LIGHTING_IP, LIGHTING_PORT_TX)
            self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # ensure that initial cue of 0.1 is correct

    def get_configuration(self) -> dict:
        return {
            "initial_playback": self.initial_playback
        }

    def enter_blackout(self):
        if DUMMY_MODE:
            return
        self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # jump to blackout cue (0.1)

    def exit_blackout(self): # doesn't seem to result in flash of incorrect lighting
        if DUMMY_MODE:
            return
        self.client.send_message(f"/pb/{self.playback}/{self.current_cue}", 1.0) # jump to previous cue

    def run_command(self, command: dict):
        if DUMMY_MODE:
            return
        match command["action"]:
            case "jump_to_cue":
                self.client.send_message(f"/pb/{self.playback}/{float(command['cue'])}", 1.0)
                self.current_cue: float = float(command['cue'])
            
            case "switch_playback":
                self.client.send_message(f"/pb/{self.playback}", 0.0)
                self.playback = int(command['playback'])
                self.client.send_message(f"/pb/{self.playback}", 0.0 if "start_in_blackout" in command and command["start_in_blackout"] else 1.0)