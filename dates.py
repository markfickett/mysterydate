import collections
import logging
import random

import enum

import voice


_RESPONSES = enum.Enum(
    'YES',
    'YES_FRIEND',
    'YES_SWITCH',
    'YES_SWITCH_FRIEND',
    'YES_CALLBACK',
    'NO_CHORE',
    'NO_CHORE_TRY_AGAIN',
    'NO_PARTY',
    'NO_BUSY',
)


_MESSAGES = {
  _RESPONSES.YES: [
    'Why yes %(host)s, I would love to come to your classy soirree.',
  ],
  _RESPONSES.YES_FRIEND: [
    "Why yes %(host)s, I would love to not only come, but jam with my BFF "
    "%(friend)s.",
  ],
  _RESPONSES.YES_SWITCH: [
    "I already said yes to %(old_host)s, but your crib is hipper. "
    "I'll see you soon, %(host)s!",
  ],
  _RESPONSES.YES_SWITCH_FRIEND: [
    "I had some plans. But %(old_host)s will have to chop some onions because "
    "%(friend)s and I have a new boat to float, and it's yours!",
  ],
  _RESPONSES.YES_CALLBACK: [
    "Thanks for the call back %(host)s, I'll totally be there!",
  ],
  _RESPONSES.NO_CHORE: [
    '%(name)s has to vacuum.',
  ],
  _RESPONSES.NO_CHORE_TRY_AGAIN: [
    "I've got to finish vacuuming. But you've got a sweet trick %(host)s! "
    "Hit me back later and let's see what I can finaegel.",
  ],
  _RESPONSES.NO_PARTY: [
    'I already said yes to %(old_host)s.',
  ],
  _RESPONSES.NO_BUSY: [
    'Sorry, I already have plans.',
  ],
}


_CallRecord = collections.namedtuple(
    'CallRecord',
    ('is_coming', 'response', 'host_name'))


class Date:
  def __init__(self, name):
    self._name = name
    self.host = None  # accessed by Host for RSVPing
    self._call_history = []
    self._parent = voice.GetRandomVoice(exclude=self._name)

  def GetName(self):
    return self._name

  def GetAndSayAnswer(self, host_name, dates, quiet=False):
    details = {
      'name': self._name,
      'host': host_name,
    }
    if self.host:
      details['old_host'] = self.host.GetName()
    filtered_history = [
        c for c in self._call_history
        if c.host_name == host_name]

    response = None
    friend = None
    is_coming = False

    if (filtered_history and
        filtered_history[-1].response == _RESPONSES.NO_CHORE_TRY_AGAIN and
        filtered_history[-1].host_name == host_name and
        random.random() < 0.9):
      response = _RESPONSES.YES_CALLBACK
      is_coming = True
    elif random.getrandbits(1) == 0:
      response = random.choice([
          _RESPONSES.NO_CHORE,
          _RESPONSES.NO_CHORE_TRY_AGAIN,
          _RESPONSES.NO_BUSY])
      is_coming = False
    elif self.host:
      if random.random() < 0.3:
        if random.getrandbits(1) == 0:
          response = _RESPONSES.YES_SWITCH
          is_coming = True
        else:
          response = _RESPONSES.YES_SWITCH_FRIEND
          is_coming = True
          friend = self._PickFriend(dates)
      else:
        response = _RESPONSES.NO_PARTY
        is_coming = False
    else:
      if random.random() < 0.05:
        response = _RESPONSES.YES_FRIEND
        is_coming = True
        friend = self._PickFriend(dates)
      else:
        response = _RESPONSES.YES
        is_coming = True

    if friend:
      details['friend'] = friend.GetName()
    self._call_history.append(_CallRecord(is_coming, response, host_name))
    self._Say(
      random.choice(_MESSAGES[response]) % details,
      response is _RESPONSES.NO_CHORE,
      quiet)
    return is_coming, friend

  def _PickFriend(self, dates):
    steals = []
    excuses = []
    untapped = []
    for date in dates:
      if date is self:
        continue
      if date.host:
        steals.append(date)
      elif date._call_history:
        excuses.append(date)
      else:
        untapped.append(date)
    r = random.random()
    if steals and r < 0.2:
      return random.choice(steals)
    elif excuses and r < 0.8:
      return random.choice(excuses)
    elif untapped:
      return random.choice(untapped)
    else:
      return random.choice(steals + excuses + untapped)

  def _Say(self, msg, as_parent, quiet):
    speaker = self._parent if as_parent else self._name
    logging.info('%s: %s', speaker, msg)
    if not quiet:
      voice.Say(msg, voice=speaker)

  def __str__(self):
    if not self._call_history:
      return '?'
    return '%s%s' % (
        self._name,
        (' partying with %s' % self.host.GetName()) if self.host else '')


def MakeDates(**kwargs):
  dates = [Date(v, **kwargs) for v in voice.VOICES]
  random.shuffle(dates)
  return dates
