import dates
import hosts
import logging
logging.basicConfig(
    format='%(levelname)s %(asctime)s %(filename)s:%(lineno)s: %(message)s',
    level=logging.INFO)


NUM_TO_WIN = 6
QUIET = True


class Player:
  def __init__(self, name):
    self.name = name
    self.dates = set()

  def GetName(self):
    return self.name


def GetPlayers():
  return [hosts.Host(name) for name in ['Kelsey', 'Billy', 'Coco', 'Mark']]


def PrintDateChoices(dates):
  msg = "Potential dates are:\n"
  for i, date in enumerate(dates):
    msg += '\t%d\t%s\n' % (i, date)
  logging.info(msg)


def SummarizePlayerStandings(players):
  logging.info(
      'How are the parties doing?\n' +
      ''.join(['\t%d\t%s\n' % (p.GetNumDates(), p.GetName()) for p in players]))


def QueryDate(dates, player):
  while True:
    s = raw_input("Who you gonna' call, %s? " % player.GetName())
    try:
      return dates[int(s)]
    except (ValueError, IndexError):
      logging.warning('Picking %r is not an option.', s)


def PlayUntilWin(players, dates):
  while True:
    for player in players:
      PrintDateChoices(dates)
      date = QueryDate(dates, player)
      logging.info('%s is calling %s...', player.GetName(), date.GetName())
      is_coming = date.GetAndSayAnswer(player.GetName(), quiet=QUIET)
      player.Rsvp(date, is_coming)
      SummarizePlayerStandings(players)
      if player.GetNumDates() >= NUM_TO_WIN:
        return player


if __name__ == '__main__':
  dates = dates.MakeDates()
  players = GetPlayers()
  try:
    winner = PlayUntilWin(players, dates)
    logging.info('%s wins!', winner.GetName())
  except KeyboardInterrupt:
    logging.info('Time to go.')
