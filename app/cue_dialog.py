
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QTabWidget, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QDialogButtonBox
from PySide6.QtGui import QIcon

from . import tools

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..show import Show
    from ..cue import Cue

class CueDialog:
    def __init__(self, show: "Show", cue: "Cue", new_cue_mode: bool = False):
        self.show: "Show" = show
        self.cue: "Cue" = cue

        self.widget: QDialog = tools.load_form("cue_dialog")
        self.widget.resize(430, 320)
        if new_cue_mode:
            self.widget.setWindowTitle("Add cue")
        else:
            self.widget.setWindowTitle(f"Editing cue {int(cue.index) if cue.index.is_integer() else cue.index}")
        self.widget.setWindowIcon(QIcon("app/resources/icon.png"))
        self.widget.setModal(True)
        self.widget.findChild(QTabWidget, "tabWidget").setCurrentIndex(0)

        self.populate_fields()

        self.widget.findChild(QDialogButtonBox, "buttonBox").accepted.connect(self.save_and_close)
        self.widget.findChild(QDialogButtonBox, "buttonBox").rejected.connect(self.widget.reject)

    def show_dialog(self):
        self.widget.show()

    def populate_fields(self):
        self.widget.findChild(QLineEdit, "descriptionLineEdit").setText(self.cue.description)
        self.widget.findChild(QLineEdit, "notesLineEdit").setText(self.cue.notes)

        commands: list[dict] = self.cue.get_commands("mixer", "enable_channels")
        if commands:
            self.widget.findChild(QCheckBox, "enableChannelsCheckBox").setChecked(True)
            self.widget.findChild(QLineEdit, "enableChannelsLineEdit").setText(" ".join([channel for command_channels in [command["channels"].split(" ") if isinstance(command["channels"], str) else command["channels"] for command in commands] for channel in command_channels]))

        commands: list[dict] = self.cue.get_commands("mixer", "disable_channels")
        if commands:
            self.widget.findChild(QCheckBox, "disableChannelsCheckBox").setChecked(True)
            self.widget.findChild(QLineEdit, "disableChannelsLineEdit").setText(" ".join([channel for command_channels in [command["channels"].split(" ") if isinstance(command["channels"], str) else command["channels"] for command in commands] for channel in command_channels]))

        commands: list[dict] = self.cue.get_commands("mixer", "set_faders_on_channels")
        if commands:
            self.widget.findChild(QCheckBox, "setFadersCheckBox").setChecked(True)
            self.widget.findChild(QLineEdit, "setFadersLineEdit").setText(" ".join([command["channels"] if isinstance(command["channels"], str) else " ".join([f"{channel}={value}" for channel, value in command["channels"].items()]) for command in commands]))

        commands: list[dict] = self.cue.get_commands("mixer", "mute_group")
        if commands:
            self.widget.findChild(QCheckBox, "muteGroupCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "muteGroupSpinBox").setValue(int(commands[0]["mute_group"]))

        commands: list[dict] = self.cue.get_commands("mixer", "unmute_group")
        if commands:
            self.widget.findChild(QCheckBox, "unmuteGroupCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "unmuteGroupSpinBox").setValue(int(commands[0]["mute_group"]))

        commands: list[dict] = self.cue.get_commands("lights", "jump_to_cue")
        if commands:
            self.widget.findChild(QCheckBox, "jumpToCueCheckBox").setChecked(True)
            self.widget.findChild(QDoubleSpinBox, "jumpToCueDoubleSpinBox").setValue(float(commands[0]["cue"]))

        commands: list[dict] = self.cue.get_commands("lights", "switch_playback")
        if commands:
            self.widget.findChild(QCheckBox, "switchToPlaybackCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "switchToPlaybackSpinBox").setValue(int(commands[0]["playback"]))

        commands: list[dict] = self.cue.get_commands("scenery", "change_backdrop_to_image")
        if commands:
            self.widget.findChild(QCheckBox, "changeBackdropToImageCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "changeBackdropToImageSpinBox").setValue(int(commands[0]["index"]))

        commands: list[dict] = self.cue.get_commands("scenery", "change_backdrop_to_video")
        if commands:
            self.widget.findChild(QCheckBox, "changeBackdropToVideoCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "changeBackdropToVideoSpinBox").setValue(int(commands[0]["index"]))

        if self.cue.get_commands("scenery", "enter_scenery_blackout"):
            self.widget.findChild(QCheckBox, "enterSceneryBlackoutCheckBox").setChecked(True)

        if self.cue.get_commands("scenery", "exit_scenery_blackout"):
            self.widget.findChild(QCheckBox, "exitSceneryBlackoutCheckBox").setChecked(True)

        commands: list[dict] = self.cue.get_commands("audio", "play")
        if commands:
            self.widget.findChild(QCheckBox, "playAudioTrackCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "trackIndexSpinBox").setValue(int(commands[0]["index"]))
            self.widget.findChild(QSpinBox, "numberOfLoopsSpinBox").setValue(int(commands[0]["loops"]) if "loops" in commands[0] else 0)
            self.widget.findChild(QDoubleSpinBox, "startTimeDoubleSpinBox").setValue(float(commands[0]["start_time"]) if "start_time" in commands[0] else 0.0)
            self.widget.findChild(QSpinBox, "fadeInSpinBox").setValue(int(commands[0]["fade_in"]) if "fade_in" in commands[0] else 0)
            self.widget.findChild(QDoubleSpinBox, "stopTimeDoubleSpinBox").setValue(float(commands[0]["stop_time"]) if "stop_time" in commands[0] else 0.0)
            self.widget.findChild(QSpinBox, "fadeOutSpinBox").setValue(int(commands[0]["fade_out"]) if "fade_out" in commands[0] else 0)

        commands: list[dict] = self.cue.get_commands("audio", "stop")
        if commands:
            self.widget.findChild(QCheckBox, "stopAudioTrackCheckBox").setChecked(True)
            self.widget.findChild(QSpinBox, "stopFadeOutSpinBox").setValue(int(commands[0]["fade_out"]) if "fade_out" in commands[0] else 0)

    @Slot()
    def save_and_close(self):
        self.cue.description = self.widget.findChild(QLineEdit, "descriptionLineEdit").text()
        self.cue.notes = self.widget.findChild(QLineEdit, "notesLineEdit").text()
        self.cue.commands = []

        if self.widget.findChild(QCheckBox, "stopAudioTrackCheckBox"): # we always want this to be the first command in a cue
            self.cue.commands.append({"subsystem": "audio", "action": "stop", "fade_out": self.widget.findChild(QSpinBox, "stopFadeOutSpinBox").value()})

        if self.widget.findChild(QCheckBox, "enableChannelsCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "mixer", "action": "enable_channels", "channels": self.widget.findChild(QLineEdit, "enableChannelsLineEdit").text()})

        if self.widget.findChild(QCheckBox, "disableChannelsCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "mixer", "action": "disable_channels", "channels": self.widget.findChild(QLineEdit, "disableChannelsLineEdit").text()})

        if self.widget.findChild(QCheckBox, "setFadersCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "mixer", "action": "set_faders_on_channels", "channels": self.widget.findChild(QLineEdit, "setFadersLineEdit").text()})

        if self.widget.findChild(QCheckBox, "muteGroupCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "mixer", "action": "mute_group", "mute_group": self.widget.findChild(QSpinBox, "muteGroupSpinBox").value()})

        if self.widget.findChild(QCheckBox, "unmuteGroupCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "mixer", "action": "unmute_group", "mute_group": self.widget.findChild(QSpinBox, "unmuteGroupSpinBox").value()})

        if self.widget.findChild(QCheckBox, "jumpToCueCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "lights", "action": "jump_to_cue", "cue": self.widget.findChild(QDoubleSpinBox, "jumpToCueDoubleSpinBox").value()})

        if self.widget.findChild(QCheckBox, "switchToPlaybackCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "lights", "action": "switch_playback", "playback": self.widget.findChild(QSpinBox, "switchToPlaybackSpinBox").value()})

        if self.widget.findChild(QCheckBox, "changeBackdropToImageCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "scenery", "action": "change_backdrop_to_image", "index": self.widget.findChild(QSpinBox, "changeBackdropToImageSpinBox").value()})

        if self.widget.findChild(QCheckBox, "changeBackdropToVideoCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "scenery", "action": "change_backdrop_to_video", "index": self.widget.findChild(QSpinBox, "changeBackdropToVideoSpinBox").value()})

        if self.widget.findChild(QCheckBox, "enterSceneryBlackoutCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "scenery", "action": "enter_scenery_blackout"})

        if self.widget.findChild(QCheckBox, "exitSceneryBlackoutCheckBox").isChecked():
            self.cue.commands.append({"subsystem": "scenery", "action": "exit_scenery_blackout"})

        if self.widget.findChild(QCheckBox, "playAudioTrackCheckBox").isChecked():
            self.cue.commands.append({
                "subsystem": "audio",
                "action": "play",
                "index": self.widget.findChild(QSpinBox, "trackIndexSpinBox").value(),
                "loops": self.widget.findChild(QSpinBox, "numberOfLoopsSpinBox").value(),
                "start_time": self.widget.findChild(QDoubleSpinBox, "startTimeDoubleSpinBox").value(),
                "fade_in": self.widget.findChild(QSpinBox, "fadeInSpinBox").value(),
                "stop_time": self.widget.findChild(QDoubleSpinBox, "stopTimeDoubleSpinBox").value(),
                "fade_out": self.widget.findChild(QSpinBox, "fadeOutSpinBox").value()
            })

        self.show.cue_list.update(self.cue)
        self.widget.accept()