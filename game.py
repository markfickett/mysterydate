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
  logging.info("Who are the hotties?")
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
  return [hosts.Host(name) for name in names]


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
      is_coming, friend = date.GetAndSayAnswer(
          player.GetName(), dates, quiet=QUIET)
      player.Rsvp(date, is_coming)
      if friend:
        player.Rsvp(friend, True)
      SummarizePlayerStandings(players)
      if player.GetNumDates() >= NUM_TO_WIN:
        return player


if __name__ == '__main__':
  dates = dates.MakeDates()
  try:
    players = GetPlayers()
    winner = PlayUntilWin(players, dates)
    if len(players) > 1:
      logging.info('%s wins!', winner.GetName())
    else:
      logging.info('I think we knew %s was going to win.', winner.GetName())
  except (KeyboardInterrupt, EOFError):
    logging.info('Time to go.')
