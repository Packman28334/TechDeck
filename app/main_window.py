
from copy import copy

from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu, QTableView, QHeaderView
from PySide6.QtCore import Qt, QAbstractTableModel, Slot, QItemSelection, QModelIndex, QObject, QEvent
from PySide6.QtGui import QIcon, QAction, QColor

from . import tools

from typing import TYPE_CHECKING
if TYPE_CHECKING:
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
    def __init__(self, show: 'Show'):
        super().__init__()
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
    def __init__(self, show: "Show"):
        self.show: "Show" = show

        self.widget: QMainWindow = tools.load_form("main_window")
        self.widget.resize(1000, 600)
        self.widget.setWindowTitle("Tech Deck")
        self.widget.setWindowIcon(QIcon("app/resources/icon.png"))

        self.table_view: QTableView = self.widget.findChild(QTableView, "cueTableView")
        self.table_event_filter: TableEventFilter = TableEventFilter()
        self.table_model: CueTableModel = CueTableModel(self.show)

        self.setup_menu()
        self.setup_table()
        self.setup_actions()

    def show_window(self):
        self.widget.show()

    def setup_menu(self):
        for name in ["File", "Edit", "Show", "Cue", "Window"]:
            menu: QMenu = self.widget.findChild(QMenuBar, "menuBar").addMenu(name)
            actions: list[str] = []
            match name:
                case "File":
                    pass
                case "Edit":
                    pass
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

    @Slot(QItemSelection, QItemSelection)
    def table_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        pass

    # TODO: make these do P2P properly

    @Slot()
    def action_move_up(self):
        if self.table_view.selectionModel().selection().indexes():
            self.show.cue_list.move_up(self.table_view.selectionModel().selection().indexes()[0].row(), 1)

    @Slot()
    def action_move_down(self):
        if self.table_view.selectionModel().selection().indexes():
            self.show.cue_list.move_down(self.table_view.selectionModel().selection().indexes()[0].row(), 1)

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
        self.widget.findChild(QAction, "actionMoveUp").triggered.connect(self.action_move_up)
        self.widget.findChild(QAction, "actionMoveDown").triggered.connect(self.action_move_down)
        self.widget.findChild(QAction, "actionDeleteCue").triggered.connect(self.action_delete_cue)
        self.widget.findChild(QAction, "actionStageCue").triggered.connect(self.action_stage_cue)
        self.widget.findChild(QAction, "actionStageNextCue").triggered.connect(self.action_stage_next_cue)
        self.widget.findChild(QAction, "actionStagePreviousCue").triggered.connect(self.action_stage_previous_cue)
        self.widget.findChild(QAction, "actionExecuteStagedCue").triggered.connect(self.action_execute_staged_cue)