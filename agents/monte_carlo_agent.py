import random
import time
import math
import copy
from agents.agent import Agent
from util import *


class MonteCarloAgent(Agent):
    """An agent utilizing Monte Carlo Tree Search.  I based much of
    this implementation off Jeff Bradberry's informative blog:
    https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""

    def __init__(self, reversi, color, **kwargs):
        self.color = color
        self.reversi = reversi
        self.sim_time = kwargs.get('sim_time', 5)

        # map states to nodes for quick lookup
        self.state_node = {}

    def reset(self):
        pass

    def observe_win(self, winner):
        pass

    def get_action(self, game_state, legal_moves):
        """Interface from class Agent.  Given a game state
        and a set of legal moves, pick a legal move and return it.
        This will be called by the Reversi game object. Does not mutate
        the game state argument."""
        # make a deep copy to keep the promise that we won't mutate
        if not legal_moves:
            return None
        game_state = copy.deepcopy(game_state)
        move = self.monte_carlo_search(game_state)
        return move

    def monte_carlo_search(self, game_state):
        """Given a game state, return the best action decided by
        using Monte Carlo Tree Search with an Upper Confidence Bound."""

        # This isn't strictly necessary for Monte Carlo to work,
        # but if we've seen this state before we can get better results by
        # reusing existing information.
        root = None
        if game_state in self.state_node:
            root = self.state_node[game_state]
        else:
            root = Node(game_state)

        # even if this is a "recycled" node we've already used,
        # remove its parent as it is now considered our root level node
        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time:
            picked_node = self.tree_policy(root)
            result = self.simulate(picked_node.game_state)
            self.back_prop(picked_node, result)
            sim_count += 1

        for child in root.children:
            wins, plays = child.get_wins_plays()
            position = child.move
            info('{}: ({}/{})'.format(position, wins, plays))
        info('{} simulations performed.'.format(sim_count))
        return self.best_action(root)

    @staticmethod
    def best_action(node):
        """Returns the best action from this game state node.
        In Monte Carlo Tree Search we pick the one that was
        visited the most.  We can break ties by picking
        the state that won the most."""
        most_plays = -float('inf')
        best_wins = -float('inf')
        best_actions = []
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if plays > most_plays:
                most_plays = plays
                best_actions = [child.move]
                best_wins = wins
            elif plays == most_plays:
                # break ties with wins
                if wins > best_wins:
                    best_wins = wins
                    best_actions = [child.move]
                elif wins == best_wins:
                    best_actions.append(child.move)

        return random.choice(best_actions)

    @staticmethod
    def back_prop(node, delta):
        """Given a node and a delta value for wins,
        propagate that information up the tree to the root."""
        while node.parent is not None:
            node.plays += 1
            node.wins += delta
            node = node.parent

        # update root node of entire tree
        node.plays += 1
        node.wins += delta

    def tree_policy(self, root):
        """Given a root node, determine which child to visit
        using Upper Confidence Bound."""
        cur_node = root

        while True:
            legal_moves = self.reversi.legal_moves(cur_node.game_state)
            if not legal_moves:
                if self.reversi.winner(cur_node.game_state) is not False:
                    # the game is won
                    return cur_node
                else:
                    # no moves, so turn passes to other player
                    next_state = self.reversi.next_state(cur_node.game_state,
                                                         None)
                    pass_node = Node(next_state)
                    cur_node.add_child(pass_node)
                    self.state_node[next_state] = pass_node
                    cur_node = pass_node
                    continue

            elif len(cur_node.children) < len(legal_moves):
                # children are not fully expanded, so expand one
                unexpanded = [
                    move for move in legal_moves
                    if move not in cur_node.moves_expanded
                ]

                # note to self: this tree of nodes includes nodes of both players, right?
                # so are you always assuming the enemy makes bad moves when you .best_child()
                # on one of their states?

                assert len(unexpanded) > 0
                move = random.choice(unexpanded)
                state = self.reversi.next_state(cur_node.game_state, move)
                n = Node(state, move)
                cur_node.add_child(n)
                self.state_node[state] = n
                return n

            else:
                # Every possible next state has been expanded, so pick one
                cur_node = self.best_child(cur_node)

        return cur_node

    def best_child(self, node):
        enemy_turn = (node.game_state[1] != self.color)
        C = 1  # 'exploration' value
        values = {}
        for child in node.children:
            wins, plays = child.get_wins_plays()
            if enemy_turn:
                # the enemy will play against us, not for us
                wins = plays - wins
            _, parent_plays = node.get_wins_plays()
            assert parent_plays > 0
            values[child] = (wins / plays) \
                + C * math.sqrt(2 * math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice

    def simulate(self, game_state):
        """Starting from the given game state, simulate
        a random game to completion, and return the profit value
        (1 for a win, 0 for a loss)"""
        WIN_PRIZE = 1
        LOSS_PRIZE = 0
        state = copy.deepcopy(game_state)
        while True:
            winner = self.reversi.winner(state)
            if winner is not False:
                if winner == self.color:
                    return WIN_PRIZE
                elif winner == opponent[self.color]:
                    return LOSS_PRIZE
                else:
                    raise ValueError

            moves = self.reversi.legal_moves(state)
            if not moves:
                # if no moves, turn passes to opponent
                state = (state[0], opponent[state[1]])
                moves = self.reversi.legal_moves(state)

            picked = random.choice(moves)
            state = self.reversi.apply_move(state, picked)


class Node:
    def __init__(self, game_state, move=None):
        self.game_state = game_state
        self.plays = 0
        self.wins = 0
        self.children = []
        self.parent = None
        self.moves_expanded = set()

        # the move that led to this child state
        self.move = move

    def add_child(self, node):
        self.children.append(node)
        self.moves_expanded.add(node.move)
        node.parent = self

    def has_children(self):
        return len(self.children) > 0

    def get_wins_plays(self):
        return self.wins, self.plays

    def __hash__(self):
        return hash(self.game_state)

    def __repr__(self):
        return 'move: {} wins: {} plays: {}'.format(self.move, self.wins,
                                                    self.plays)

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.game_state == other.game_state
