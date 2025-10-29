
class SpotlightSubsystem:
    def __init__(self):
        self.current_guide: str = "Spotlight off"

    def get_configuration(self) -> dict:
        return {}

    @property
    def state(self) -> dict:
        return {}
    
    @state.setter
    def state(self, new_state: dict):
        pass

    def enter_blackout(self):
        pass

    def exit_blackout(self):
        pass

    def run_command(self, command: dict):
        match command["action"]:
            case "change_guide":
                self.current_guide = command["guide"]