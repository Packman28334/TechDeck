
import copy

from cue import Cue

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
    
    def __str__(self) -> str:
        return str([str(cue) for cue in self.cues])

    def __getitem__(self, index: int) -> Cue:
        return self.cues[index]
    
    def __setitem__(self, index: int, value: Cue):
        self.cues[index] = value

    def __len__(self) -> int:
        return len(self.cues)

    def __iter__(self) -> CueListIterator:
        return CueListIterator(self)

    def append(self, cue: Cue) -> None:
        self.cues.append(cue)

    def insert(self, position: int, cue: Cue) -> None:
        self.cues.insert(position, cue)

    def pop(self, position: int) -> Cue:
        return self.cues.pop(position)

    @staticmethod
    def deserialize(cues: list[dict]) -> list[Cue]:
        out = []
        for cue in cues:
            out.append(Cue(
                cue["description"],
                cue["commands"],
                blackout=cue["blackout"]
            ))
        return out

    def serialize(self) -> list[dict]:
        out: list[dict] = []
        for cue in self.cues:
            out.append({
                "description": cue.description,
                "commands": cue.commands,
                "blackout": cue.blackout
            })
        return out
    
    @classmethod
    def create_from_serialized(cls, cues: list[dict]):
        return cls(cls.deserialize(cues))

    def copy(self, old_position: int, new_position: int) -> None:
        self.cues.insert(new_position, copy.deepcopy(self.cues[old_position]))
    
    def move(self, old_position: int, new_position: int) -> None:
        if new_position > old_position:
            self.cues.insert(new_position-1, self.cues.pop(old_position))
        elif new_position < old_position:
            self.cues.insert(new_position+1, self.cues.pop(old_position))

    def move_up(self, position: int, amount: int) -> None:
        self.move(position, position-amount)

    def move_down(self, position: int, amount: int) -> None:
        self.move(position, position+amount)