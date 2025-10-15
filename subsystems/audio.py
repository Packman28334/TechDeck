
import pygame, time, os
from config import DISABLE_AUDIO

if not DISABLE_AUDIO:
    pygame.mixer.init()
    pygame.init()

class AudioSubsystem:
    def __init__(self):
        self.stop_at: float = -1.0
        self.fade_out: int = -1

    def get_configuration(self) -> dict:
        return {}
    
    # def update_polling_tasks(self):
    #     if pygame.mixer.music.get_busy() and self.stop_at > 0:
    #         if time.time() > self.stop_at:
    #             if self.fade_out > 0:
    #                 pygame.mixer.music.fadeout(self.fade_out)
    #             else:
    #                 pygame.mixer.music.stop()

    def update_polling_tasks(self):
        if DISABLE_AUDIO:
            return
        if pygame.mixer.music.get_busy() and self.stop_at > 0:
            if self.fade_out > 0:
                if time.time() > self.stop_at - self.fade_out/1000:
                    pygame.mixer.music.fadeout(self.fade_out)
            else:
                if time.time() > self.stop_at:
                    pygame.mixer.music.stop()

    def list_audio(self) -> list[str]:
        if os.path.exists("_working_show") and os.path.isdir("_working_show"):
            if os.path.exists("_working_show/audio_library") and os.path.isdir("_working_show/audio_library"):
                return os.listdir("_working_show/audio_library")
        return []

    def find_filename_by_index(self, index: int) -> str:
        for track in self.list_audio():
            try:
                if int(track.split(" ")[0]) == index:
                    return track
            except ValueError:
                pass
        return ""

    def find_track_from_command(self, command: dict) -> str:
        if "filename" in command and os.path.exists(f"_working_show/audio_library/{command['filename']}"):
            return "_working_show/audio_library/"+command["filename"]
        else:
            return "_working_show/audio_library/"+self.find_filename_by_index(int(command["index"]))

    def run_command(self, command: dict):
        match command["action"]:
            case "play":
                if DISABLE_AUDIO:
                    return
                try:
                    pygame.mixer.music.load(self.find_track_from_command(command))
                except FileNotFoundError:
                    print(f"[ERROR] Failed to find music file {self.find_track_from_command(command)}")
                    return
                pygame.mixer.music.play(
                    int(command["loops"]) if "loops" in command and command["loops"] else 0,
                    float(command["start_time"]) if "start_time" in command and command["start_time"] else 0,
                    int(command["fade_in"]) if "fade_in" in command and command["fade_in"] else 0
                )
                if "stop_time" in command and command["stop_time"]:
                    self.stop_at = time.time() + float(command["stop_time"])
                else:
                    self.stop_at = -1.0
                if "fade_out" in command and command["fade_out"]:
                    self.fade_out = int(command["fade_out"])
                else:
                    self.fade_out = -1
            
            case "stop":
                if DISABLE_AUDIO:
                    return
                if "fade_out" in command and command["fade_out"]:
                    pygame.mixer.music.fadeout(int(command["fade_out"]))
                else:
                    pygame.mixer.music.stop()
                pygame.mixer.music.unload()