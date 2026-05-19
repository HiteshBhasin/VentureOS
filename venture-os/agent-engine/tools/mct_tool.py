import numpy as np


class Mct:
    def __init__(self, state, action, parent=None) -> None:
        self.state = state
        self.action = action
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def __str__(self) -> str:
        return f"MCT(state={self.state}, action={self.action})"

    def _ucb1(self, node: "Mct", c: float = 1.414) -> float:
        """Upper Confidence Bound score for a child node."""
        if node.visits == 0:
            return float("inf")

        child = node.value / node.visits + c * np.sqrt(
            np.log(self.visits) / node.visits
        )
        return child

    def Selection(self, tree: Mct) -> Mct:
        """Walk the tree from root using UCB1 until an unexpanded (leaf) node is found."""
        node = tree
        while node.children:
            node = max(node.children, key=lambda c: self._ucb1(c))
        return node

    def Expansion(self, leaf: Mct) -> Mct:
        #         Search tree grows by generating a new child of selected
        #         node.this node represent a new state that is not previously explored
        new_child_node = Mct(state=None, action=None, parent=leaf)
        leaf.children.append(new_child_node)
        return new_child_node

    def Simulation(self, child: Mct):
        import random 
        # After Expansion, the algorithm picks a child node arbitrarily, and it simulates entire game from selected node until it reaches the resulting state of the game. If nodes are picked randomly during the play out, it is called light play out. You can also opt for heavy play out by writing quality heuristics or evaluation functions.
        state = child.state.copy()
        while not self.terminal_state(state):
            ready_task = {}
            if len(ready_task)==0:
                break
            task = 
            

    def Reward(self):
        pass

    def Backpropagation(self, result, child: Mct):
        pass
