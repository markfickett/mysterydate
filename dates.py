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
    'NO_ANNOYED',
)


_MESSAGES = {
  _RESPONSES.YES: [
    'Why yes %(host)s, I would love to come to your classy soirree.',
    'Awesome dude. Catch you on the flip side.',
    'Sure. Cool. Yeah.',
    "Hey %(host)s. What's that? Game night? Count me in!",
    "I sure could use a night on the town. Let's go %(host)s!",
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
    "Hit me back later and let's see what I can finagle.",
  ],
  _RESPONSES.NO_PARTY: [
    'I already said yes to %(old_host)s.',
    "Arr %(host)s, I be already swillin' the bilgewaters with me mess mates.",
  ],
  _RESPONSES.NO_BUSY: [
    'Sorry, I already have plans.',
    'I must regretfully decline your invite.',
    "I'm on vacation, we'll have to try some other time.",
    'What is this "party" you speak of, %(host)s? I detest such frivolity.',
    "Voicemail for %(name)s. Leave a message and I'll get back to you when I "
    "have finished whatever important thing I'm doing. Click. Hahaha sucker.",
  ],
  _RESPONSES.NO_ANNOYED: [
    'Yo buzz of %(host)s.',
    'Back it up a notch %(host)s.',
    'Please just peace out.',
    "No news is bad news for me, %(host)s. Still can't come.",
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
        random.random() < (0.5 if self.host else 0.9)):
      response = _RESPONSES.YES_CALLBACK
      is_coming = True
    elif (filtered_history and not filtered_history[-1].is_coming and
          random.random() < 0.8):
      response = _RESPONSES.NO_ANNOYED
      is_coming = False
    elif random.random() < 0.6:
      excuses = [_RESPONSES.NO_BUSY]
      if not self.host:
        excuses += [_RESPONSES.NO_CHORE, _RESPONSES.NO_CHORE_TRY_AGAIN]
      response = random.choice(excuses)
      is_coming = False
    elif self.host:
      if self.host.GetName() == host_name:
        response = _RESPONSES.NO_ANNOYED
        is_coming = False
      if random.random() < 0.3:
        if random.getrandbits(1) == 0:
          response = _RESPONSES.YES_SWITCH
          is_coming = True
        else:
          response = _RESPONSES.YES_SWITCH_FRIEND
          is_coming = True
          friend = self._PickFriend(dates, host_name)
      else:
        response = _RESPONSES.NO_PARTY
        is_coming = False
    else:
      if random.random() < 0.2:
        response = _RESPONSES.YES_FRIEND
        is_coming = True
        friend = self._PickFriend(dates, host_name)
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

  def _PickFriend(self, dates, host_name):
    steals = []
    excuses = []
    untapped = []
    for date in dates:
      if date is self or (date.host and date.host.GetName() == host_name):
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
      everyone = steals + excuses + untapped
      return random.choice(everyone) if everyone else None

  def _Say(self, msg, as_parent, quiet):
    speaker = self._parent if as_parent else self._name
    if quiet:
      logging.info('%s: %s', speaker, msg)
    else:
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
