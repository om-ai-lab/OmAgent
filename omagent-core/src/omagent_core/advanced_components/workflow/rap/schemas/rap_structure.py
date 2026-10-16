from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import itertools
import numpy as np
from typing import Callable

class Node:
    id_iter = itertools.count()

    @classmethod
    def reset_id(cls):
        cls.id_iter = itertools.count()

    def __init__(self, state: str, action: str, parent: "Optional[Node]" = None,
                 fast_reward: float = 0., fast_reward_details=None,
                 is_terminal: bool = False, calc_q: Callable[[list[float]], float] = np.max):
        """
        A node in the MCTS search tree

        Args:
            state: The current state
            action: The action from parent node to current node
            parent: The parent node, None if root
            fast_reward: Estimation of the reward of the last step
            is_terminal: Whether current state is terminal
            calc_q: How to calculate Q value from histories
        """
        self.id = next(Node.id_iter)
        if fast_reward_details is None:
            fast_reward_details = {}
        self.cum_rewards: list[float] = []
        self.fast_reward = self.reward = fast_reward
        self.fast_reward_details = fast_reward_details
        self.is_terminal = is_terminal
        self.action = action
        self.state = state
        self.parent = parent
        self.children: 'Optional[list[Node]]' = None
        self.calc_q = calc_q
        self.depth = parent.depth + 1 if parent else 0

    @property
    def Q(self) -> float:
        if self.state is None:
            return self.fast_reward
        return self.calc_q(self.cum_rewards)

class SearchTree:
    def __init__(self, data_input):
        self.root = Node(state=data_input, action=None)
        self.data_input = data_input

class MCTS:
    w_exp: float = 1.

    @staticmethod
    def uct_select(node: Node):
        return max(node.children, key=MCTS.uct)
    
    @staticmethod
    def uct(node: Node):
        return node.Q + MCTS.w_exp * np.sqrt(np.log(len(node.parent.cum_rewards)) / max(1, len(node.cum_rewards))) 