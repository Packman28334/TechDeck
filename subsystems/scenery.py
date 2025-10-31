
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..p2p_networking import P2PNetworkManager

IMAGE_FILE_EXTENSIONS: tuple[str] = (".jpg", ".jpeg", ".png", ".gif", ".webp")
VIDEO_FILE_EXTENSIONS: tuple[str] = (".mp4", ".m4v", ".avi")

class ScenerySubsystem:
    def __init__(self, p2p_network_manager: "P2PNetworkManager"):
        self.p2p_network_manager: "P2PNetworkManager" = p2p_network_manager
        self.media_filename: str = ""
        self.is_video: bool = False

    def get_configuration(self) -> dict:
        return {}

    @property
    def state(self) -> dict:
        return {"media_filename": self.media_filename, "is_video": self.is_video}
    
    @state.setter
    def state(self, new_state: dict):
        self.media_filename = new_state["media_filename"]
        self.is_video = new_state["is_video"]

    # these functions are unsed as blackout handles itself on the frontend
    def enter_blackout(self):
        pass

    def exit_blackout(self):
        pass

    def list_backdrops(self) -> list[str]:
        if os.path.exists("_working_show") and os.path.isdir("_working_show"):
            if os.path.exists("_working_show/backdrop_library") and os.path.isdir("_working_show/backdrop_library"):
                return os.listdir("_working_show/backdrop_library")
        return []

    def find_filename_by_index(self, index: int) -> str:
        for backdrop in self.list_backdrops():
            try:
                if (backdrop.lower().endswith(IMAGE_FILE_EXTENSIONS) and not self.is_video) or (backdrop.lower().endswith(VIDEO_FILE_EXTENSIONS) and self.is_video):
                    if int(backdrop.split(" ")[0]) == index:
                        return backdrop
            except ValueError:
                pass
        return ""

    def find_backdrop_from_command(self, command: dict) -> str:
        if "filename" in command and os.path.exists(f"_working_show/backdrop_library/{command['filename']}"):
            return command["filename"]
        else:
            return self.find_filename_by_index(int(command["index"]))

    def broadcast_new_backdrop(self):
        self.p2p_network_manager.broadcast_to_servers("backdrop_changed", {"filename": self.media_filename, "is-video": self.is_video})
        self.p2p_network_manager.broadcast_to_client("backdrop_changed", {"filename": self.media_filename, "is-video": self.is_video})

    def run_command(self, command: dict):
        match command["action"]:
            case "change_backdrop_to_image":
                self.is_video = False
                self.media_filename = self.find_backdrop_from_command(command)
                self.broadcast_new_backdrop()
            
            case "change_backdrop_to_video":
                self.is_video = True
                self.media_filename = self.find_backdrop_from_command(command)
                self.broadcast_new_backdrop()