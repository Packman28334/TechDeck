
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton
from PySide6.QtCore import Slot
from PySide6.QtGui import QIcon, QAction, QPixmap

from typing import Callable

from . import tools

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main import MainController

class LaunchWindow:
    def __init__(self, controller: "MainController"):
        self.controller: "MainController" = controller

        self.widget: QMainWindow = tools.load_form("launch_window")
        self.widget.resize(525, 270)
        self.widget.setWindowTitle("Tech Deck 2")
        self.widget.setWindowIcon(QIcon("app/resources/icon.png"))

        self.widget.findChild(QLabel, "logoLabel").setPixmap(QPixmap("app/resources/logo.png"))

        self.setup_actions()

    def show_window(self):
        self.widget.show()

    def close_window(self):
        self.widget.close()

    @Slot()
    def action_quit(self):
        self.close_window()

    @Slot()
    def action_connect_to_network(self):
        self.controller.connect_to_network()

    @Slot()
    def action_new(self):
        self.controller.new_show()

    @Slot()
    def action_open(self):
        self.controller.open_show()

    def setup_actions(self):
        ACTION_MAPPING: dict[str, Callable] = {
            "actionQuit": self.action_quit,
            "actionConnectToNetwork": self.action_connect_to_network,
            "actionNew": self.action_new,
            "actionOpen": self.action_open
        }
        for action_name, action_callable in ACTION_MAPPING.items():
            self.widget.findChild(QAction, action_name).triggered.connect(action_callable)