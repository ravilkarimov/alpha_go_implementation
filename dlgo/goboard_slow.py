import copy
from typing import Dict, List, Optional, Set

from dlgo.gotypes import Player, Point


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
    def __init__(
        self, color: Player, stones: List[Point], liberties: List[Point]
    ) -> None:
        self.color: Player = color
        self.stones: Set[Point] = set(stones)
        self.liberties: Set[Point] = set(liberties)

    def remove_liberty(self, point: Point) -> None:
        self.liberties.remove(point)

    def add_liberty(self, point: Point) -> None:
        self.liberties.add(point)

    # Returns new Go_string contaning stones from two strings
    def merge_with(self, go_string: "Go_String") -> "Go_String":
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return Go_String(
            self.color,
            list(combined_stones),
            list((self.liberties | go_string.liberties) - combined_stones),
        )

    @property
    def num_liberties(self) -> int:
        return len(self.liberties)

    def __eq__(self, __o) -> bool:
        return (
            isinstance(__o, Go_String)
            and self.color == __o.color
            and self.stones == __o.stones
            and self.liberties == __o.liberties
        )


class Board:
    # An empty board is initialized as an empty grid
    # with specified number of rows and columns
    def __init__(self, num_rows=19, num_cols=19):
        self.num_rows = num_rows
        self.num_cols = num_cols
        # TODO: write types
        self._grid: Dict[Point, Optional[Go_String]] = {}

    def is_on_grid(self, point: Point) -> bool:
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    # Returns the content of a point on the board: a Player
    # if a stone is on that point or None
    def get(self, point: Point) -> Optional[Player]:
        string = self._grid.get(point)
        return None if string is None else string.color

    # Returns the entire string of stones at a point: a GoString
    # if a stone is on that point or None
    def get_go_string(self, point: Point) -> Optional[Go_String]:
        string = self._grid.get(point)
        return None if string is None else string

    def _remove_string(self, string: Go_String):
        for point in string.stones:
            for neighbor in point.neighbours():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                # Removing a string can create liberties for other strings.
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            self._grid[point] = None

    def place_stone(self, player: Player, point: Point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        # Examine direct neighbors of this point.
        for neighbor in point.neighbours():
            if not self.is_on_grid(neighbor):
                continue
            # TODO: write types
            neighbor_string = self.get_go_string(neighbor)
            if not neighbor_string:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            elif neighbor_string not in adjacent_opposite_color:
                adjacent_opposite_color.append(neighbor_string)
        new_string = Go_String(player, [point], liberties)

        # Merge any adjacent strings of the same color
        for same_color_string in adjacent_same_color:
            new_string = new_string.merge_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        # Reduce liberties of any adjacent strings of the opposite color.
        for other_color_string in adjacent_opposite_color:
            other_color_string.remove_liberty(point)
        # If any opposite-color strings now have zero liberties, remove them.
        for other_color_string in adjacent_opposite_color:
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)


class GameState:
    def __init__(
        self,
        board: Board,
        next_player: Player,
        previous: "Optional[GameState]",
        move: Optional[Move],
    ):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        self.last_move = move

    # Returns the new GameState after applying the move
    def apply_move(self, move: Move) -> "GameState":
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size=19) -> "GameState":
        board = Board(board_size, board_size)
        return cls(board, Player.black, None, None)

    def is_over(self) -> bool:
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = (
            self.previous_state.last_move if self.previous_state else None
        )
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass
