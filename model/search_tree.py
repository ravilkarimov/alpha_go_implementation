from model.types import Node
from model.utils import (
    best_uct,
    fully_expanded,
    is_root,
    non_terminal,
    pick_random,
    pick_unvisited,
    resources_left,
    result,
    update_stats,
)


# main function for the Monte Carlo Tree Search
def monte_carlo_tree_search(root: Node) -> Node:

    time, computational_power = 0, 0
    while resources_left(time, computational_power):
        leaf = traverse(root)
        simulation_result = rollout(leaf)
        backpropagate(leaf, simulation_result)

    return best_child(root)


# function for node traversal
def traverse(node: Node) -> Node:
    while fully_expanded(node):
        node = best_uct(node)

    # in case no children are present / node is terminal
    return pick_unvisited(node.children) or node


# function for the result of the simulation
def rollout(node: Node):
    while non_terminal(node):
        node = rollout_policy(node)
    return result(node)


# function for randomly selecting a child node
def rollout_policy(node: Node) -> Node:
    return pick_random(node.children)


# function for backpropagation
def backpropagate(node: Node, result):
    if is_root(node):
        return
    node.stats = update_stats(node, result)
    backpropagate(node.parent)


# function for selecting the best child
# node with highest number of visits
def best_child(node: Node) -> Node:
    # pick child with highest number of visits
    pass
