
from pathlib import Path
from copy import copy

from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu, QTableView, QHeaderView, QFileDialog
from PySide6.QtCore import Qt, QAbstractTableModel, Slot, QItemSelection, QModelIndex, QObject, QEvent
from PySide6.QtGui import QIcon, QAction, QColor

from typing import Callable

from .cue_dialog import CueDialog
from . import tools

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..main import MainController
    from ..show import Show
    from ..cue import Cue

show: Show | None = None

class TableEventFilter(QObject):
    def __init__(self):
        super().__init__()

    def eventFilter(self, watched, event: QEvent):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
                event.ignore()
                return True
        return super().eventFilter(watched, event)

class CueTableModel(QAbstractTableModel):
    def __init__(self, window: MainWindow, show: 'Show'):
        super().__init__()
        self.window: MainWindow = window
        self.show: 'Show' = show
        self.cue_list: list["Cue"] = copy(self.show.cue_list.cues) # we have QTableWidget at home
        self.show.cue_change_callbacks.append(self.callback)
        self.show.cue_list.cue_change_callbacks.append(self.callback)

    def callback(self):
        current_cue_uuids: list[str] = [cue.uuid for cue in self.cue_list]
        new_cue_uuids: list[str] = [cue.uuid for cue in self.show.cue_list]
        for idx, cue in enumerate(self.cue_list): # remove old cues
            if cue.uuid not in new_cue_uuids:
                self.beginRemoveRows(QModelIndex(), idx, idx)
                self.cue_list.remove(cue)
                self.endRemoveRows()
        for idx, cue in enumerate(self.show.cue_list.cues): # add new cues
            if cue.uuid not in current_cue_uuids:
                self.beginInsertRows(QModelIndex(), idx, idx)
                self.cue_list.insert(idx, cue)
                self.endInsertRows()
        for idx, cue in enumerate(self.cue_list): # move cues
            if idx != new_cue_uuids.index(cue.uuid):
                self.beginMoveRows(QModelIndex(), idx, idx, QModelIndex(), new_cue_uuids.index(cue.uuid)+1)
                self.cue_list.remove(cue)
                self.cue_list.insert(new_cue_uuids.index(cue.uuid), cue)
                self.endMoveRows()
        # update content
        self.cue_list = copy(self.show.cue_list.cues)
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.cue_list)-1, 3))
        self.window.update_title()

    def rowCount(self, /, parent = ...):
        return len(self.show.cue_list)

    def columnCount(self, /, parent = ...):
        return 4

    def data(self, index, /, role = ...):
        if not index.isValid():
            return None
        
        match role:
            case Qt.ItemDataRole.DisplayRole:
                match index.column():
                    case 0:
                        return None
                    case 1:
                        cue_number: float = self.cue_list[index.row()].index
                        if cue_number.is_integer():
                            return str(int(cue_number))
                        else:
                            return str(cue_number)
                    case 2:
                        return str(self.cue_list[index.row()].description)
                    case 3:
                        return str(self.cue_list[index.row()].notes)
            case Qt.ItemDataRole.BackgroundRole:
                if index.row() == self.show.staged_cue:
                    return QColor("#1800a8")
                if index.row() == self.show.current_cue:
                    return QColor("green")
        return None

    def headerData(self, section, orientation, /, role = ...):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["", "ID", "Description", "Notes"][section]
        return super().headerData(section, orientation, role)

class MainWindow:
    def __init__(self, controller: "MainController", show: "Show"):
        self.controller: "MainController" = controller
        self.show: "Show" = show

        self.widget: QMainWindow = tools.load_form("main_window")
        self.widget.resize(1000, 600)
        self.update_title()
        self.widget.setWindowIcon(QIcon("app/resources/icon.png"))

        self.table_view: QTableView = self.widget.findChild(QTableView, "cueTableView")
        self.table_event_filter: TableEventFilter = TableEventFilter()
        self.table_model: CueTableModel = CueTableModel(self, self.show)

        self.setup_menu()
        self.setup_table()
        self.setup_actions()

    def show_window(self):
        self.widget.show()

    def close_window(self):
        self.widget.close()

    def setup_menu(self):
        for name in ["File", "Show", "Cue", "Window"]:
            menu: QMenu = self.widget.findChild(QMenuBar, "menuBar").addMenu(name)
            actions: list[str] = []
            match name:
                case "File":
                    actions: list[str] = ["actionNew", "", "actionOpen", "", "actionSave", "actionSaveAs"]
                case "Show":
                    actions: list[str] = ["actionStageNextCue", "actionStagePreviousCue", "actionExecuteStagedCue", "", "actionAddCue"]
                case "Cue":
                    actions: list[str] = ["actionStageCue", "", "actionEditCue", "actionDeleteCue", "actionMoveUp", "actionMoveDown"]
                case "Window":
                    pass
            for action in actions:
                if action:
                    menu.addAction(self.widget.findChild(QAction, action))
                else:
                    menu.addSeparator()

    def setup_table(self):
        self.table_view.installEventFilter(self.table_event_filter)

        self.table_view.setModel(self.table_model)

        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        header: QHeaderView = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table_view.selectionModel().selectionChanged.connect(self.table_selection_changed)

    def update_title(self):
        if self.show.file_path:
            self.widget.setWindowTitle(f"{Path(self.show.file_path).name}{'*' if self.show.cue_list.unsaved else ''} | Tech Deck 2")
        else:
            self.widget.setWindowTitle("Tech Deck 2")

    @Slot(QItemSelection, QItemSelection)
    def table_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        pass

    # TODO: make these do P2P properly

    @Slot()
    def action_save(self):
        if self.show.file_path:
            self.show.save(self.show.file_path)
        else:
            self.action_save_as()

    @Slot()
    def action_save_as(self):
        dest_path: str = QFileDialog.getSaveFileName(caption="Save as...", dir="./shows", filter="Tech Deck shows (*.tdshw)")[0]
        if dest_path:
            if not dest_path.endswith(".tdshw"):
                dest_path += ".tdshw"
            self.show.file_path = dest_path
            self.show.save(self.show.file_path)

    @Slot()
    def action_open(self):
        self.controller.open_show()

    @Slot()
    def action_new(self):
        if self.show.cue_list.unsaved:
            pass # TODO
        self.controller.new_show()

    @Slot()
    def action_add_cue(self):
        #self._open_dialog: CueDialog = CueDialog(self.show)
        #self._open_dialog.show_dialog()
        pass # TODO

    @Slot()
    def action_move_up(self):
        if self.table_view.selectionModel().selection().indexes():
            self.show.cue_list.move_up(self.table_view.selectionModel().selection().indexes()[0].row(), 1)

    @Slot()
    def action_move_down(self):
        if self.table_view.selectionModel().selection().indexes():
            self.show.cue_list.move_down(self.table_view.selectionModel().selection().indexes()[0].row(), 1)

    @Slot()
    def action_edit_cue(self):
        if self.table_view.selectionModel().selection().indexes():
            self._open_dialog: CueDialog = CueDialog(self.show, self.show.cue_list[self.table_view.selectionModel().selection().indexes()[0].row()])
            self._open_dialog.show_dialog()

    @Slot()
    def action_delete_cue(self):
        if self.table_view.selectionModel().selection().indexes():
            self.show.cue_list.pop(self.table_view.selectionModel().selection().indexes()[0].row())

    @Slot()
    def action_stage_cue(self):
        self.show.stage_cue(self.table_view.selectionModel().selection().indexes()[0].row())

    @Slot()
    def action_stage_next_cue(self):
        self.show.stage_next_cue()

    @Slot()
    def action_stage_previous_cue(self):
        self.show.stage_previous_cue()

    @Slot()
    def action_execute_staged_cue(self):
        self.show.execute_staged_cue()

    def setup_actions(self):
        ACTION_MAPPING: dict[str, Callable] = {
            "actionSave": self.action_save,
            "actionSaveAs": self.action_save_as,
            "actionOpen": self.action_open,
            "actionNew": self.action_new,
            "actionAddCue": self.action_add_cue,
            "actionMoveUp": self.action_move_up,
            "actionMoveDown": self.action_move_down,
            "actionEditCue": self.action_edit_cue,
            "actionDeleteCue": self.action_delete_cue,
            "actionStageCue": self.action_stage_cue,
            "actionStageNextCue": self.action_stage_next_cue,
            "actionStagePreviousCue": self.action_stage_previous_cue,
            "actionExecuteStagedCue": self.action_execute_staged_cue
        }
        for action_name, action_callable in ACTION_MAPPING.items():
            self.widget.findChild(QAction, action_name).triggered.connect(action_callable)