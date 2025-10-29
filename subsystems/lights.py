
from pythonosc.udp_client import SimpleUDPClient

from config import DUMMY_MODE, LIGHTING_IP, LIGHTING_PORT_TX

class LightingSubsystem:
    def __init__(self, initial_playback: int):
        self.initial_playback: int = initial_playback
        self.playback: int = initial_playback
        self.current_cue: float = 0.1

        self.blackout: bool = False
        self.switch_to_playback_after_blackout: int | None = None
        self.jump_to_cue_after_blackout: float | None = None

        if not DUMMY_MODE:
            self.client: SimpleUDPClient = SimpleUDPClient(LIGHTING_IP, LIGHTING_PORT_TX)
            self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # ensure that initial cue of 0.1 is correct

    def get_configuration(self) -> dict:
        return {
            "initial_playback": self.initial_playback
        }

    @property
    def state(self) -> dict:
        return {"current_cue": self.current_cue, "playback": self.playback, "blackout": self.blackout}

    @state.setter
    def state(self, new_state: dict):
        self.current_cue = new_state["current_cue"]
        self.playback = new_state["playback"]
        self.blackout = new_state["blackout"]

    def enter_blackout(self):
        if DUMMY_MODE:
            return
        self.client.send_message(f"/pb/{self.playback}/0.1", 1.0) # jump to blackout cue (0.1)

    def exit_blackout(self): # doesn't seem to result in flash of incorrect lighting
        if DUMMY_MODE:
            return
        
        if self.switch_to_playback_after_blackout != None:
            self.client.send_message(f"/pb/{self.playback}", 0.0)
            self.playback = self.switch_to_playback_after_blackout
            self.client.send_message(f"/pb/{self.playback}", 1.0)
            self.switch_to_playback_after_blackout = None

        if self.jump_to_cue_after_blackout != None:
            self.client.send_message(f"/pb/{self.playback}/{self.jump_to_cue_after_blackout}", 1.0)
            self.current_cue: float = self.jump_to_cue_after_blackout
            self.jump_to_cue_after_blackout = None

        self.client.send_message(f"/pb/{self.playback}/{self.current_cue}", 1.0) # jump to desired cue

    def run_command(self, command: dict):
        if DUMMY_MODE:
            return
        match command["action"]:
            case "jump_to_cue":
                if self.blackout:
                    self.jump_to_cue_after_blackout = float(command['cue'])
                else:
                    self.client.send_message(f"/pb/{self.playback}/{float(command['cue'])}", 1.0)
                    self.current_cue: float = float(command['cue'])
            
            case "switch_playback":
                if self.blackout:
                    self.switch_to_playback_after_blackout = int(command['playback'])
                else:
                    self.client.send_message(f"/pb/{self.playback}", 0.0)
                    self.playback = int(command['playback'])
                    self.client.send_message(f"/pb/{self.playback}", 1.0)