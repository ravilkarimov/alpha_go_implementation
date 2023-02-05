import itertools
import random

from dlgo.gotypes import Player, Point


def to_python(player_state: Player) -> str:
    if player_state is None:
        return "None"
    return str(Player.black) if player_state == Player.black else str(Player.white)


MAX63 = 0x7FFFFFFFFFFFFFFF
table = {}
empty_board = 0

for row, col in itertools.product(range(1, 20), range(1, 20)):
    for state in (Player.black, Player.white):
        code = random.randint(0, MAX63)
        table[Point(row, col), state] = code

print("from .gotypes import Player, Point")
print("")
print("__all__ = ['HASH_CODE', 'EMPTY_BOARD']")
print("")
print("HASH_CODE = {")
for (pt, state), hash_code in table.items():
    print("    (%r, %s): %r," % (pt, to_python(state), hash_code))
print("}")
print("")
print("EMPTY_BOARD = %d" % (empty_board,))
