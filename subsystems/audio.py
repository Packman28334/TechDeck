
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

    def run_command(self, command: dict):
        match command["action"]:
            case "play":
                if DISABLE_AUDIO:
                    return
                pygame.mixer.music.load(f"_working_show/audio_library/{command['filename']}")
                pygame.mixer.music.play(
                    int(command["loops"]) if "loops" in command else 0,
                    float(command["start_time"]) if "start_time" in command else 0,
                    int(command["fade_in"]) if "fade_in" in command else 0
                )
                if "stop_time" in command:
                    self.stop_at = time.time() + float(command["stop_time"])
                else:
                    self.stop_at = -1.0
                if "fade_out" in command:
                    self.fade_out = int(command["fade_out"])
                else:
                    self.fade_out = -1
            
            case "stop":
                if DISABLE_AUDIO:
                    return
                if "fade_out" in command:
                    pygame.mixer.music.fadeout(command["fade_out"])
                else:
                    pygame.mixer.music.stop()
                pygame.mixer.music.unload()