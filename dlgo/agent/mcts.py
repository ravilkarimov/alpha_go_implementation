import math
import random
from typing import List, Optional

from dlgo import agent
from dlgo.goboard import GameState, Move
from dlgo.gotypes import Player


class MCTSNode(object):
    def __init__(self, game_state, parent=None, move=None) -> None:
        # The current state of the game at this node
        self.game_state: GameState = game_state
        self.parent: Optional[MCTSNode] = parent
        # The last move led to this node
        self.move: Optional[Move] = move
        self.win_counts = {
            Player.black: 0,
            Player.white: 0,
        }
        self.num_rollouts = 0
        self.children: List[MCTSNode] = []
        self.unvisited_moves = game_state.legal_moves()

    def add_random_child(self) -> "MCTSNode":
        index = random.randint(0, len(self.unvisited_moves) - 1)
        new_move = self.unvisited_moves.pop(index)
        new_game_state = self.game_state.apply_move(new_move)
        new_node = MCTSNode(new_game_state, self, new_move)
        self.children.append(new_node)
        return new_node

    def record_win(self, winner: Player) -> None:
        self.win_counts[winner] += 1
        self.num_rollouts += 1

    def can_add_child(self) -> bool:
        return len(self.unvisited_moves) > 0

    def is_terminal(self) -> bool:
        return self.game_state.is_over()

    def winning_frac(self, player) -> float:
        return self.win_counts[player] / self.num_rollouts


class MCTSAgent(agent.Agent):
    def select_move(self, game_state: GameState) -> Move:

        # Start MCTS algorithm
        root = MCTSNode(game_state)

        for _ in range(self.num_round):
            node = root
            while not node.can_add_child() and not node.is_terminal():
                node = self.select_child(node)

            if node.can_add_child():
                # Adds new child node into the tree
                node = node.add_random_child()

            # Simulates random game from this node
            winner = self.simulate_random_game(node.game_state)

            while node is not None:
                # Propagates the score back up the tree
                node.record_win(winner)
                node = node.parent

        # Select a move after completing MCTS rollouts
        best_move = None
        best_pct = -1.0
        for child in root.children:
            child_pct = child.winning_pct(game_state.next_player)
            if child_pct > best_pct:
                best_pct = child_pct
                best_move = child.move
        return best_move

    def select_child(self, node: MCTSNode):
        total_rollouts = sum(child.num_rollouts for child in node.children)
        best_score = -1
        best_child = None
        for child in node.children:
            score = uct_score(
                total_rollouts,
                child.num_rollouts,
                child.winning_frac(node.game_state.next_player),
                self.temperature,
            )
            if score > best_score:
                best_score = score
                best_child = child
        return best_child


def uct_score(
    parent_rollouts: int, child_rollouts: int, win_pct: float, temperature: float
) -> float:
    exploration = math.sqrt(math.log(parent_rollouts) / child_rollouts)
    return win_pct + temperature * exploration
