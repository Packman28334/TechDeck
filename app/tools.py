
import sys

from PySide6.QtCore import QFile, QIODevice, QObject, QEvent
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QApplication

from typing import Callable

app: QApplication | None = None

def load_form(form_name: str) -> QWidget:
    file: QFile = QFile(f"app/forms/{form_name}.ui")
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise Exception(f"Failed to open form '{form_name}': {file.errorString()}")
    loader: QUiLoader = QUiLoader()
    form: QWidget = loader.load(file)
    file.close()
    if not form:
        raise Exception(f"Failed to load form '{form_name}: {loader.errorString()}")
    return form

def begin_app_load():
    global app
    app = QApplication(sys.argv)
    return app

def run_app():
    global app
    if app:
        sys.exit(app.exec())