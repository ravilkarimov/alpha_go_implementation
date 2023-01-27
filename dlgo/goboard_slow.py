from typing import Self, Set

from dlgo.gotypes import Point


# Clients generally won’t call the Move constructor directly.
# Instead, you usually call Move.play, Move.pass_turn,
# or Move.resign to construct an instance of a move
class Move:
    # Any action a player can play o a turn:
    # is_play, is_pass, is_resign
    def __init__(self, point=None, is_pass=False, is_resign=False) -> None:
        assert point is not None
        self.point = point
        self.is_play = self.point is not None
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point):
        # this move places stone to the board
        return Move(point=point)

    @classmethod
    def pass_turn(cls):
        # this move passes
        return Move(is_pass=True)

    @classmethod
    def resign(cls):
        # this move resigns the current game
        return Move(is_resign=True)


# Go strings are a chain of connected stones of the same color
class Go_String:
    def __init__(self, color, stones: Set[Point], liberties: Set[Point]) -> None:
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)

    def remove_liberty(self, point: Point) -> None:
        self.liberties.remove(point)

    def add_liberty(self, point: Point) -> None:
        self.liberties.add(point)

    # Returns new Go_string contaning stones from two strings
    def merge_with(self, go_string: Self) -> Self:
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return Go_String(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones,
        )

    @property
    def num_liberties(self) -> int:
        return len(self.liberties)

    def __eq__(self, __o: Self) -> bool:
        return (
            isinstance(__o, Go_String)
            and self.color == __o.color
            and self.stones == __o.stones
            and self.liberties == __o.liberties
        )
