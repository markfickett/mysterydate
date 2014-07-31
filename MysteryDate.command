#!/usr/bin/env python
import logging

import game


if __name__ == '__main__':
  try:
    players = game.GetPlayers()
    while True:
      game.RunGame(players)
      again = raw_input('Start a new game? [Yy/Nn]: ')
      if not again.strip().lower().startswith('y'):
        break
  except (KeyboardInterrupt, EOFError):
    logging.info("Well, that's over quickly.")
