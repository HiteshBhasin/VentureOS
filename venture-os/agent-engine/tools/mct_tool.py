import random
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

    def selection(self, tree: Mct) -> Mct:
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
        # After Expansion, the algorithm picks a child node arbitrarily, and it simulates entire game from selected node until it reaches the resulting state of the game. If nodes are picked randomly during the play out, it is called light play out. You can also opt for heavy play out by writing quality heuristics or evaluation functions.
        state = child.state

        while not self.is_terminal(state):
            action = random.choice(self.get_possible_actions(state))
            state = self.apply_action(state, action)
        # Return the result of the simulation (e.g., win/loss/draw)
        if state == "Completed":
            return 1  # Win
        elif state in ["Failed", "Cancelled", "TimedOut", "Error"]:
            return -1  # Loss
        else:
            return 0  # Draw or non-terminal state

    def Backpropagation(self, result, child: Mct):
        node = child
        while node is not None:
            node.visits += 1
            node.value += result
            node = node.parent

    def search(self, root: "Mct", n_iterations: int = 1000) -> "Mct":
        """Run MCTS for N iterations and return the best child of the root.

        Each iteration runs the four MCTS steps:
          1. Selection  – walk the tree using UCB1 to find a leaf
          2. Expansion  – add a new child to that leaf
          3. Simulation – roll out a random playout from the new child
          4. Backpropagation – propagate the reward back up the tree

        The best child is the one with the most visits (most robust estimate).
        """
        for _ in range(n_iterations):
            # Step 1 – Selection
            leaf = self.selection(root)

            # Step 2 – Expansion (only expand non-terminal nodes)
            if leaf.state is not None and not self.is_terminal(leaf.state):
                child = self.Expansion(leaf)
            else:
                child = leaf

            # Step 3 – Simulation
            result = self.Simulation(child)

            # Step 4 – Backpropagation
            self.Backpropagation(result, child)

        # Return the child of root with the highest visit count
        if not root.children:
            return root
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child

    def is_terminal(self, state):
        # Implement logic to check if the state is terminal
        terminal_state = [
            "Completed",
            "Running",
            "Failed",
            "Cancelled",
            "TimedOut",
            "Error",
        ]
        if state in terminal_state:
            return True
        return False

    def get_possible_actions(
        self, state
    ):  # Implement logic to return possible actions for the given state
        if state == "NotStarted":
            return ["Start"]
        elif state == "Running":
            return ["Complete", "Fail", "Cancel", "Timeout", "Error"]
        else:
            return []

    def apply_action(
        self, state, action
    ):  # Implement logic to apply the action to the state and return the new state
        if state == "NotStarted" and action == "Start":
            return "Running"
        elif state == "Running":
            if action == "Complete":
                return "Completed"
            elif action == "Fail":
                return "Failed"
            elif action == "Cancel":
                return "Cancelled"
            elif action == "Timeout":
                return "TimedOut"
            elif action == "Error":
                return "Error"
        else:
            return state
