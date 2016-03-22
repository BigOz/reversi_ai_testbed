import sys


class Agent:
    """An abstract class defining the interface for a Reversi agent."""

    def __init__(self, reversi, color):
        raise NotImplementedError

    def get_action(self, game_state, legal_moves):
        raise NotImplementedError
