from dataclasses import dataclass
from enum import Enum


class Player(Enum):
    black = 1
    white = 2

    @property
    def other(self):
        # After a player places a stone,
        # we should switch the color by calling the other method
        return Player.black if self == Player.white else Player.white


# Coordinates on the board
@dataclass(frozen=True)
class Point:
    row: int
    col: int

    def neighbors(self):
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]
