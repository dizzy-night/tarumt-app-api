from attrs import define
from enum import Enum, auto


# TODO: check for more
class Department(Enum):
    LIB = auto()
    FOCS = auto()
    DSA = auto()
    DQA = auto()
    DFIN = auto()
    DECA = auto()
    DACE = auto()
    CPE = auto()


@define
class Announcement:
    title: str
    id: str    # guid
    type: str  # TODO: find out
    sender: Department
    is_read: bool
    

