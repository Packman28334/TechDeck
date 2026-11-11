
from PySide6.QtWidgets import QFileDialog

import os

from app import LaunchWindow, MainWindow, begin_app_load, run_app
from show import Show
from p2p_networking import p2p_network_manager

begin_app_load()

class MainController:
    def __init__(self):
        self.window: LaunchWindow = LaunchWindow(self)
        self.window.show_window()

        self.show: Show | None = None

    def new_show(self):
        self.show: Show = Show.new()
        self.window.close_window()
        self.window: MainWindow = MainWindow(self, self.show)
        self.window.show_window()

    def open_show(self):
        show_path: str = QFileDialog.getOpenFileName(caption="Select show", dir="./shows", filter="Tech Deck shows (*.tdshw)")[0]
        if os.path.exists(show_path) and show_path.endswith(".tdshw"):
            self.show: Show = Show.load(show_path)
            self.window.close_window()
            self.window: MainWindow = MainWindow(self, self.show)
            self.window.show_window()

    def connect_to_network(self):
        pass

if __name__ == '__main__':
    controller: MainController = MainController()
    run_app()
    p2p_network_manager.shutdown()