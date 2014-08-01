import logging
import random

import dates
import hosts


logging.basicConfig(
    format='%(levelname)s %(asctime)s %(filename)s:%(lineno)s: %(message)s',
    level=logging.INFO)


_NUM_TO_WIN = 6
_QUIET = False


def GetPlayers():
  logging.info("Who are you hotties?")
  names = set()
  while True:
    name = raw_input('Enter your name (blank if we have everyone): ').strip()
    if name:
      if name in names:
        logging.info('Come on, %s is already playing.', name)
      else:
        logging.info('%s is in!', name)
        names.add(name)
    if not name:
      if names:
        logging.info({
          3: "Three's a party!",
          2: "Two's company.",
          1: 'I really hope you win!',
        }.get(len(names), 'Yeehaw!'))
        break
      else:
        logging.info("You can't play like this.")
  players = [hosts.Host(name) for name in names]
  random.shuffle(players)
  return players


def _PrintDateChoices(potential_dates):
  msg = "Potential dates are:\n"
  for i, date in enumerate(potential_dates):
    msg += '\t%d\t%s\n' % (i, date)
  logging.info(msg)


def _SummarizePlayerStandings(players):
  logging.info(
      'How are the parties doing?\n' +
      ''.join(['\t%s\t%d\t%s\n' % (
          p.GetName(),
          p.GetNumDates(),
          ', '.join(p.GetDateNames())) for p in players]))


def _QueryDate(potential_dates, player):
  while True:
    s = raw_input("Who you gonna' call, %s? " % player.GetName())
    try:
      return potential_dates[int(s)]
    except (ValueError, IndexError):
      logging.warning('Picking %r is not an option.', s)


def PlayUntilWin(players, potential_dates):
  while True:
    for player in players:
      _PrintDateChoices(potential_dates)
      date = _QueryDate(potential_dates, player)
      logging.info('%s is calling %s...', player.GetName(), date.GetName())
      is_coming, friend = date.GetAndSayAnswer(
          player, potential_dates, quiet=_QUIET)
      player.Rsvp(date, is_coming)
      if friend:
        player.Rsvp(friend, True)
      _SummarizePlayerStandings(players)
      if player.GetNumDates() >= _NUM_TO_WIN:
        return player


def RunGame(players):
  for player in players:
    player.ClearDates()
  potential_dates = dates.MakeDates()
  for date in potential_dates:
    date.AddEnemies(potential_dates)
  winner = PlayUntilWin(players, potential_dates)
  if len(players) > 1:
    logging.info('%s wins!', winner.GetName())
  else:
    logging.info('I think we knew %s was going to win.', winner.GetName())
