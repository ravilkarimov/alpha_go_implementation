import copy
from typing import FrozenSet, Optional, Tuple

from dlgo import zobrist
from dlgo.gotypes import Player, Point


# Clients generally won’t call the Move constructor directly.
# Instead, you usually call Move.play, Move.pass_turn,
# or Move.resign to construct an instance of a move
class Move:
    # Any action a player can play o a turn:
    # is_play, is_pass, is_resign
    def __init__(self, point=None, is_pass=False, is_resign=False) -> None:
        # assert point is not None
        self.point = point
        self.is_play = self.point is not None
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point: Point):
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
class GoString:
    def __init__(
        self, color: Player, stones: FrozenSet[Point], liberties: FrozenSet[Point]
    ) -> None:
        self.color = color
        self.stones = stones
        self.liberties = liberties

    # The without_liberty method replaces the previous remove_liberty method
    def without_liberty(self, point: Point) -> "GoString":
        new_liberties = self.liberties - {point}
        return GoString(self.color, self.stones, new_liberties)

    def with_liberty(self, point: Point) -> "GoString":
        new_liberties = self.liberties | {point}
        return GoString(self.color, self.stones, new_liberties)

    # Returns new Go_string contaning stones from two strings
    def merge_with(self, go_string: "GoString") -> "GoString":
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones,
        )

    @property
    def num_liberties(self) -> int:
        return len(self.liberties)

    def __eq__(self, __o) -> bool:
        return (
            isinstance(__o, GoString)
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
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD

    def is_on_grid(self, point: Point) -> bool:
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    # Returns the content of a point on the board: a Player
    # if a stone is on that point or None
    def get(self, point: Point) -> Optional[Player]:
        string = self._grid.get(point)
        return None if string is None else string.color

    # Returns the entire string of stones at a point: a GoString
    # if a stone is on that point or None
    def get_go_string(self, point: Point) -> Optional[GoString]:
        string = self._grid.get(point)
        return None if string is None else string

    def _replace_string(self, new_string: GoString) -> None:
        for point in new_string.stones:
            self._grid[point] = new_string

    def _remove_string(self, string: GoString):
        for point in string.stones:
            for neighbor in point.neighbors():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                # Removing a string can create liberties for other strings.
                if neighbor_string is not string:
                    self._replace_string(neighbor_string.with_liberty(point))
            self._grid[point] = None
            self._hash ^= zobrist.HASH_CODE[point, string.color]

    def place_stone(self, player: Player, point: Point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        # Examine direct neighbors of this point.
        for neighbor in point.neighbors():
            if not self.is_on_grid(neighbor):
                continue
            # TODO: write types
            neighbor_string = self.get_go_string(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            elif neighbor_string not in adjacent_opposite_color:
                adjacent_opposite_color.append(neighbor_string)

        new_string = GoString(player, frozenset([point]), frozenset(liberties))

        # Merge any adjacent strings of the same color
        for same_color_string in adjacent_same_color:
            new_string = new_string.merge_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

        # Apply the hash code for this point and player
        self._hash ^= zobrist.HASH_CODE[point, player]

        # Reduce liberties of any adjacent strings of the opposite color.
        for other_color_string in adjacent_opposite_color:
            replacement_string = other_color_string.without_liberty(point)
            if replacement_string.num_liberties:
                self._replace_string(other_color_string.without_liberty(point))
            else:
                # If any opposite-color strings now have zero liberties, remove them.
                self._remove_string(other_color_string)

    def zobrist_hash(self):
        return self._hash


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
        if previous is None:
            self.previous_states: FrozenSet[Tuple[Player, int]] = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states
                | {(previous.next_player, previous.board.zobrist_hash())}
            )
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
    def new_game(cls, board_size=19):
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

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        # Capturing game state and checking for illegal moves 39
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_violate_ko(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board.zobrist_hash())
        return next_situation in self.previous_states

    def is_valid_move(self, move: Move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is not None
            and not self.is_move_self_capture(self.next_player, move)
            and not self.does_move_violate_ko(self.next_player, move)
        )
