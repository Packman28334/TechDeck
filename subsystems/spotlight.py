
import os
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from ..p2p_networking import P2PNetworkManager

ICONS: tuple[str] = ("SL", "SR", "CS")

class SpotlightSubsystem:
    def __init__(self, p2p_network_manager: "P2PNetworkManager"):
        self.p2p_network_manager: "P2PNetworkManager" = p2p_network_manager
        self.current_icon: Literal["SL"] | Literal["SR"] | Literal["CS"] | Literal[""] = ""
        self.current_guide: str = ""

        self.blackout: bool = False
        self.icon_after_blackout: Literal["SL"] | Literal["SR"] | Literal["CS"] | Literal[""] | None = None
        self.guide_after_blackout: str | None = None

    def get_configuration(self) -> dict:
        return {}

    @property
    def state(self) -> dict:
        return {"current_icon": self.current_icon, "current_guide": self.current_guide}
    
    @state.setter
    def state(self, new_state: dict):
        self.current_icon = new_state["current_icon"]
        self.current_guide = new_state["current_guide"]

    def enter_blackout(self):
        self.blackout = True

    def exit_blackout(self):
        self.blackout = False
        if self.guide_after_blackout != None:
            self.current_guide = self.guide_after_blackout
            self.current_icon = self.icon_after_blackout
            self.broadcast_new_guide()
            self.guide_after_blackout = None
            self.icon_after_blackout = None

    def broadcast_new_guide(self):
        self.p2p_network_manager.broadcast_to_servers("spotlight_changed", {"icon": self.current_icon, "guide": self.current_guide})
        self.p2p_network_manager.broadcast_to_client("spotlight_changed", {"icon": self.current_icon, "guide": self.current_guide})

    def run_command(self, command: dict):
        match command["action"]:
            case "change_guide":
                if self.blackout:
                    self.icon_after_blackout = ""
                    if "icon" in command and command["icon"] in ICONS:
                        self.icon_after_blackout = command["icon"]
                    self.guide_after_blackout = command["guide"]
                else:
                    self.current_icon = ""
                    if "icon" in command and command["icon"] in ICONS:
                        self.current_icon = command["icon"]
                    self.current_guide = command["guide"]
                    self.broadcast_new_guide()