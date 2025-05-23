
class SpotlightSubsystem:
    def __init__(self):
        self.current_guide: str = "Spotlight off"

    def get_configuration(self) -> dict:
        return {}

    def enter_blackout(self):
        pass

    def exit_blackout(self):
        pass

    def run_command(self, command: dict):
        match command["id"]:
            case "change_guide":
                self.current_guide = command["guide"]