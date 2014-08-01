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
    'NO_ENEMY',
)


# TODO: Custom messages for the singing voices:
#     Bad News
#     Bells
#     Cellos
#     Good News
#     Pipe Organ
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
    "Hellz yeah mofo. And I'm bringing my bitch %(friend)s!",
    'Indubitably! Mayhaps I shalt convey my esteeemed associate %(friend)s to '
    'accompany me to yonder festivus.',
    "I've been looking for a way to get %(friend)s in bed with me. Finally "
    "an opportunity. We'll be there.",
    'Yes, but only if I can bring my conjoined twin %(friend)s.',
  ],
  _RESPONSES.YES_SWITCH: [
    "I already said yes to %(old_host)s, but your crib is hipper. "
    "I'll see you soon, %(host)s!",
    'Unfortunately I already told %(old_host)s I... am coming to your party!',
  ],
  _RESPONSES.YES_SWITCH_FRIEND: [
    "I had some plans. But %(old_host)s will have to chop some onions because "
    "%(friend)s and I have a new boat to float, and it's yours!",
  ],
  _RESPONSES.YES_CALLBACK: [
    "Thanks for the call back %(host)s, I'll totally be there!",
    "Oh hey %(host)s, yeah, I've cleared my calendar.",
  ],
  _RESPONSES.NO_CHORE: [
    '%(name)s has to ' + excuse for excuse in [
        'vacuum.',
        "braid the dog's hair.",
        "fill the cistern on Saturday nights.",
        "learn to fold a towel before learning to make the sushi.",
        "tie-dye my underpants.",
        "massage the hamburger for three hours.",
        "bathe in milk.",
        "count the drug mo... I mean vacuum.",
    ]
  ],
  _RESPONSES.NO_CHORE_TRY_AGAIN: [
    "I've got to finish vacuuming. But you've got a sweet trick %(host)s! "
    "Hit me back later and let's see what I can finagle.",
    "I've got to finish alphabetizing my neckties. Please call back later.",
    "I've got to finish preserving the sheep's eyes in formaldehyde. Hit me "
    "back in a few.",
    "Bees, bees, everywhere! Call the doctor! Then call me back.",
    "This horse won't shoe itself. Um. Holla' back in a few hours.",
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
  _RESPONSES.NO_ENEMY: [
    'No way am I going to a party with %(enemy)s!',
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
    self._enemies = set()

  def GetName(self):
    return self._name

  def AddEnemies(self, dates):
    if random.random() < 0.1:
      self._enemies.update(random.sample(
          [d for d in dates if d is not self],
          random.randint(2, 8)))

  def GetAndSayAnswer(self, host, dates, quiet=False):
    details = {
      'name': self._name,
      'host': host.GetName(),
    }
    if self.host:
      details['old_host'] = self.host.GetName()
    filtered_history = [
        c for c in self._call_history
        if c.host_name == host.GetName()]

    response = None
    friend = None
    is_coming = False
    enemies = host.CheckDates(self._enemies)
    enemy = random.choice(list(enemies)) if enemies else None

    if enemy:
      response = _RESPONSES.NO_ENEMY
      is_coming = False
      details['enemy'] = enemy.GetName()
    elif (filtered_history and
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
      if self.host.GetName() == host.GetName():
        response = _RESPONSES.NO_ANNOYED
        is_coming = False
      if random.random() < 0.3:
        if random.getrandbits(1) == 0:
          response = _RESPONSES.YES_SWITCH
          is_coming = True
        else:
          response = _RESPONSES.YES_SWITCH_FRIEND
          is_coming = True
          friend = self._PickFriend(dates, host.GetName())
      else:
        response = _RESPONSES.NO_PARTY
        is_coming = False
    else:
      if random.random() < 0.2:
        response = _RESPONSES.YES_FRIEND
        is_coming = True
        friend = self._PickFriend(dates, host.GetName())
      else:
        response = _RESPONSES.YES
        is_coming = True

    if friend:
      details['friend'] = friend.GetName()
    self._call_history.append(_CallRecord(is_coming, response, host.GetName()))
    self._Say(
      self._GetMessageTemplate(response) % details,
      response is _RESPONSES.NO_CHORE,
      quiet)
    return is_coming, friend

  def _GetMessageTemplate(self, response):
    return random.choice(_MESSAGES[response])

  def _PickFriend(self, dates, host_name):
    steals = []
    excuses = []
    untapped = []
    for date in dates:
      if (date is self or
          (date.host and date.host.GetName() == host_name) or
          date in self._enemies):
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


class _CustomMessageDate(Date):

  def __init__(self, voice_name, message_overrides, **kwargs):
    Date.__init__(self, voice_name, **kwargs)
    self._messages = message_overrides

  def _GetMessageTemplate(self, response):
    return random.choice(self._messages.get(response, _MESSAGES[response]))


_HYSTERICAL_MESSAGES = {
  _RESPONSES.YES : [
      'I love to laugh!',
      'The more I laugh, the more I fill with glee!'],
  _RESPONSES.YES_FRIEND : [
      'The more the glee, the more %(friend)s and I are a merrier we!'],
  _RESPONSES.NO_CHORE : [
      '%(name)s is learning to twitter like a bird.',
      'Can you believe %(name)s is hissing and fizzing like a snake?'],
  _RESPONSES.NO_CHORE_TRY_AGAIN : [
      "Then there's the kind what can't make up their mind.",
      "I've got to let go with a ho ho ho."],
  _RESPONSES.NO_PARTY : ["We're a merrier we!"],
  _RESPONSES.NO_BUSY : ["I can't hide it inside."],
  _RESPONSES.NO_ANNOYED : [
      "It's getting worse every year.",
      "It's embarrassing!"],
  _RESPONSES.NO_ENEMY : ['%(enemy)s laughs through their teeth goodness sake.'],
}
_HYSTERICAL_MESSAGES[_RESPONSES.YES_CALLBACK] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES]
_HYSTERICAL_MESSAGES[_RESPONSES.YES_SWITCH] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES]
_HYSTERICAL_MESSAGES[_RESPONSES.YES_SWITCH_FRIEND] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES_FRIEND]


def MakeDates(**kwargs):
  dates = []
  custom_voices = set()
  for voice_name, overrides in (
      ('Hysterical', _HYSTERICAL_MESSAGES),):
    dates.append(_CustomMessageDate(voice_name, overrides))
    custom_voices.add(voice_name)
  dates += [Date(v, **kwargs) for v in (voice.VOICES_SET - custom_voices)]
  random.shuffle(dates)
  return dates
