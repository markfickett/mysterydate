import logging
import random
import voice


class Date:
  def __init__(self, name):
    self.name = name
    self.host = None

  def GetName(self):
    return self.name

  def GetAndSayAnswer(self, host_name, quiet=False):
    if random.getrandbits(1) == 1:
      self._Say("Great, I'll be there!", quiet)
      return True
    else:
      details = {
        'host': host_name,
      }
      self._Say("Sorry %(host)s, I can't make it." % details, quiet)
      return False

  def _Say(self, msg, quiet):
    if quiet:
      logging.info('%s: %s', self.name, msg)
    else:
      voice.Say(msg, voice=self.name)

  def __str__(self):
    return '%s%s' % (
        self.name,
        (' partying with %s' % self.host.GetName()) if self.host else '')


def MakeDates(**kwargs):
  dates = [Date(v, **kwargs) for v in voice.VOICES]
  random.shuffle(dates)
  return dates
