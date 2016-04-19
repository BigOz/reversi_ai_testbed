#!/usr/bin/env python3
import time
from agents import QLearningAgent
from game.reversi import Reversi
from math import floor
from util import *
from agents import ExperienceReplay

import sys

SNAPSHOT_AMNT = 1000  # this frequently, save a snapshot of the states
STOP_EXPLORING = 0.5  # after how many games do we set epsilon to 0?


def main():
    amount = 40000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        amount = int(sys.argv[1])

    reversi = Reversi(size=6, WhiteAgent=QLearningAgent,
            BlackAgent=QLearningAgent, silent=True, learning_enabled=True, model_weights='neural/q_weights')

    black_mem = ExperienceReplay(1)
    white_mem = ExperienceReplay(1)
    reversi.black_agent.set_memory(black_mem)
    reversi.white_agent.set_memory(white_mem)

    epsilon = 1.0
    end_exploration = max(1, floor(amount * STOP_EXPLORING))
    print('exploration will halt at {} games.'.format(end_exploration))

    start = time.time()
    try:
        for i in range(1, amount + 1):
            print('playing game {}/{} ({:2.2f}%)'.format(i, amount, i * 100 / amount))
            print('\tsetting epsilon to {:.2f}'.format(epsilon))
            reversi.white_agent.set_epsilon(epsilon)
            reversi.black_agent.set_epsilon(epsilon)
            mem_len = min(i, 2000)
            print('\tsetting memory size to {}'.format(mem_len))
            black_mem.set_replay_len(mem_len)
            white_mem.set_replay_len(mem_len)
            reversi.play_game()

            if i % SNAPSHOT_AMNT == 0:
                amnt = i / SNAPSHOT_AMNT
                reversi.white_agent.save_weights('_' + str(amnt))
                reversi.black_agent.save_weights('_' + str(amnt))

            epsilon -= (1 / end_exploration)
            epsilon = max(epsilon, 0.01)
    except KeyboardInterrupt:
        print('Stopping.  Will save weights before quitting.')

    seconds = time.time() - start
    print('time: {:.2f} minutes. per game: {:.2f}ms.'.format(
        seconds / 60.0, (seconds / float(i)) * 1000.0))
    reversi.white_agent.save_weights('')
    reversi.black_agent.save_weights('')


if __name__ == "__main__":
    main()
