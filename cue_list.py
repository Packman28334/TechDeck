
import copy
import re
from typing import TYPE_CHECKING

from cue import Cue

if TYPE_CHECKING:
    from show import Show

class CueListIterator:
    def __init__(self, cue_list: "CueList"):
        self.cue_list: "CueList" = cue_list
        self.position: int = -1
    
    def __next__(self):
        self.position += 1
        if self.position == len(self.cue_list):
            raise StopIteration
        return self.cue_list[self.position]

class CueList:
    def __init__(self, cues: list[Cue] = []):
        self.cues: list[Cue] = cues
        self.show: "Show" | None = None

    def set_show(self, show: "Show"):
        self.show = show
        for cue in self.cues:
            cue.show = show

    def _cues_changed(self):
        if self.show:
            if self.show.p2p_network_manager.is_master_node:
                self.show.p2p_network_manager.broadcast_to_servers("cue_list_changed", {"cue_list": self.serialize()})
            for cue in self.cues: # if the cues were changed, it's possible that there is a cue without a show reference. that is catastrophic. fix it.
                cue.show = self.show
            #self.show.save(self.show.title)
            self.show.p2p_network_manager.broadcast_to_client("cue_list_changed", {"cue_list": self.serialize()})

    def _single_cue_changed(self, index: int):
        if self.show:
            if self.show.p2p_network_manager.is_master_node:
                self.show.p2p_network_manager.broadcast_to_servers("cue_edited", {"index": index, "cue": self.cues[index].serialize()})
            self.cues[index].show = self.show # make sure the cue has a show reference
            #self.show.save(self.show.title)
            self.show.p2p_network_manager.broadcast_to_client("cue_edited", {"index": index, "cue": self.cues[index].serialize()})

    def __str__(self) -> str:
        return str([str(cue) for cue in self.cues])

    def __getitem__(self, index: int) -> Cue:
        return self.cues[index]
    
    def __setitem__(self, index: int, value: Cue):
        self.cues[index] = value
        self._single_cue_changed(index)

    def __len__(self) -> int:
        return len(self.cues)

    def __iter__(self) -> CueListIterator:
        return CueListIterator(self)

    def append(self, cue: Cue) -> None:
        self.cues.append(cue)
        self._cues_changed()

    def insert(self, position: int, cue: Cue) -> None:
        self.cues.insert(position, cue)
        self._cues_changed()

    def pop(self, position: int) -> Cue:
        cue: Cue = self.cues.pop(position)
        self._cues_changed()
        return cue

    def index(self, cue: Cue) -> Cue:
        return self.cues.index(cue)

    @staticmethod
    def deserialize(cues: list[dict]) -> list[Cue]:
        out = []
        for cue in cues:
            out.append(Cue.deserialize(cue))
        return out

    def deserialize_to_self(self, cues: list[dict]):
        self.cues = self.deserialize(cues)
        for cue in self.cues:
            cue.show = self.show
        self._cues_changed()

    def serialize(self) -> list[dict]:
        out: list[dict] = []
        for cue in self.cues:
            out.append(cue.serialize())
        return out
    
    @classmethod
    def create_from_serialized(cls, cues: list[dict]):
        return cls(cls.deserialize(cues))

    def copy(self, old_position: int, new_position: int) -> None:
        self.cues.insert(new_position, copy.deepcopy(self.cues[old_position]))
        self._cues_changed()
    
    def move(self, old_position: int, new_position: int, _suppress_change: bool = False) -> None:
        if new_position > old_position:
            self.cues.insert(new_position-1, self.cues.pop(old_position))
        elif new_position < old_position:
            self.cues.insert(new_position+1, self.cues.pop(old_position))
        if not _suppress_change:
            self._cues_changed()

    def move_up(self, position: int, amount: int, _suppress_change: bool = False) -> None:
        self.move(position, position-amount-1, _suppress_change=_suppress_change)

    def move_down(self, position: int, amount: int, _suppress_change: bool = False) -> None:
        self.move(position, position+amount+1, _suppress_change=_suppress_change)

    def move_multiple_up(self, positions: list[int], amount: int) -> None:
        positions = sorted(positions)
        for position in positions:
            self.move_up(position, amount, _suppress_change=True)
        self._cues_changed()

    def move_multiple_down(self, positions: list[int], amount: int) -> None:
        positions = sorted(positions, reverse=True)
        for position in positions:
            self.move_down(position, amount, _suppress_change=True)
        self._cues_changed()
    
    def import_cue_sheet(self, cue_sheet_contents: str):
        self.cues = []
        #cells: list[str] = re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', cue_sheet_contents.replace("\r\n", ",")) # https://stackoverflow.com/a/2787979
        cells = cue_sheet_contents.replace("\r\n", "\t").split("\t")
        if len(cells) % 12:
            print("ERROR: Malformed cue sheet. Import cannot continue.")
            return
        rows: list[list[str]] = [cells[idx:idx+12] for idx in range(12, len(cells), 12)]
        for row in rows:
            print(row)
            cue = Cue(row[3], [], row[10], row[9] == "TRUE")
            self.cues.append(cue)
        self._cues_changed()