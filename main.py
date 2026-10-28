
from app import MainWindow, begin_app_load, run_app
from show import Show
from p2p_networking import p2p_network_manager

begin_app_load()

show: Show | None = None

show = Show.load("test")
main_window: MainWindow = MainWindow(show)
main_window.show_window()

if __name__ == '__main__':
    run_app()
    p2p_network_manager.shutdown()