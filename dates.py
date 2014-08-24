import collections
import itertools
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
    'NO_POLICE',
    'NO_ENEMY',
)


_MESSAGES = {
  _RESPONSES.YES: (
    'Why yes %(host)s, I would love to come to your classy soirree.',
    'Awesome dude. Catch you on the flip side.',
    'Sure. Cool. Yeah.',
    "Hey %(host)s. What's that? Game night? Count me in!",
    "I sure could use a night on the town. Let's go %(host)s!",
  ),
  _RESPONSES.YES_FRIEND: (
    "Why yes %(host)s, I would love to not only come, but jam with my BFF "
    "%(friend)s.",
    "Hellz yeah mofo. And I'm bringing my bitch %(friend)s!",
    'Indubitably! Mayhaps I shalt convey my esteeemed associate %(friend)s to '
    'accompany me to yonder festivus.',
    "I've been looking for a way to get %(friend)s in bed with me. Finally "
    "an opportunity. We'll be there.",
    'Yes, but only if I can bring my conjoined twin %(friend)s.',
  ),
  _RESPONSES.YES_SWITCH: (
    "I already said yes to %(old_host)s, but your crib is hipper. "
    "I'll see you soon, %(host)s!",
    'Unfortunately I already told %(old_host)s I... am coming to your party!',
  ),
  _RESPONSES.YES_SWITCH_FRIEND: (
    "I had some plans. But %(old_host)s will have to chop some onions because "
    "%(friend)s and I have a new boat to float, and it's yours!",
  ),
  _RESPONSES.YES_CALLBACK: (
    "Thanks for the call back %(host)s, I'll totally be there!",
    "Oh hey %(host)s, yeah, I've cleared my calendar.",
  ),
  _RESPONSES.NO_CHORE: [
    '%(name)s has to ' + excuse for excuse in (
        'vacuum.',
        "braid the dog's hair.",
        "fill the cistern on Saturday nights.",
        "learn to fold a towel before learning to make the sushi.",
        "tie-dye my underpants.",
        "massage the hamburger for three hours.",
        "bathe in milk.",
        "count the drug mo... I mean vacuum.",
    )
  ],
  _RESPONSES.NO_CHORE_TRY_AGAIN: (
    "I've got to finish vacuuming. But you've got a sweet trick %(host)s! "
    "Hit me back later and let's see what I can finagle.",
    "I've got to finish alphabetizing my neckties. Please call back later.",
    "I've got to finish preserving the sheep's eyes in formaldehyde. Hit me "
    "back in a few.",
    "Bees, bees, everywhere! Call the doctor! Then call me back.",
    "This horse won't shoe itself. Um. Holla' back in a few hours.",
  ),
  _RESPONSES.NO_PARTY: (
    'I already said yes to %(old_host)s.',
    "Arr %(host)s, I be already swillin' the bilgewaters with me mess mates.",
  ),
  _RESPONSES.NO_BUSY: (
    'Sorry, I already have plans.',
    'I must regretfully decline your invite.',
    "I'm on vacation, we'll have to try some other time.",
    'What is this "party" you speak of, %(host)s? I detest such frivolity.',
    "Voicemail for %(name)s. Leave a message and I'll get back to you when I "
    "have finished whatever important thing I'm doing. Click. Hahaha sucker.",
  ),
  _RESPONSES.NO_ANNOYED: (
    'Yo buzz of %(host)s.',
    'Back it up a notch %(host)s.',
    'Please just peace out.',
    "No news is bad news for me, %(host)s. Still can't come.",
  ),
  _RESPONSES.NO_POLICE: (
    "I'm calling the police. This has to stop now.",
    "It's you're own grave you're digging.",
    'You know you have a restraining order now?',
    'Please talk to my lawyer.',
  ),
  _RESPONSES.NO_ENEMY: (
    'No way am I going to a party with %(enemy)s!',
  ),
}


_CallRecord = collections.namedtuple(
    'CallRecord',
    ('is_coming', 'response', 'host_name', 'time_index'))


class _InvitationAndResponse:
  def __init__(self, host, dates, time_index, quiet):
    self.host = host
    self.dates = dates
    self.time_index = time_index
    self.filtered_history = []

    self.quiet = quiet

    self.is_coming = None
    self.response = None
    self.details = {}
    self.friend = None


def _NoopIfHasResponse(decider_fn):
  def NoopIfHasResponse(self, invitation_and_response):
    return (
        invitation_and_response if invitation_and_response.response
        else decider_fn(self, invitation_and_response))
  return NoopIfHasResponse


class Date:
  _by_call_code = {}
  _blacklist = set()

  def __init__(self, name, call_code):
    self._name = name
    self._call_code = call_code
    self._call_history = []
    self._parent = voice.GetRandomVoice(exclude=self._name)
    self._enemies = set()

    # accessed by Host for RSVPing
    self.host = None
    self.rsvp_time = None

    self._by_call_code[self._call_code] = self  # TODO weakref?

  def GetName(self):
    return self._name

  def GetCallCode(self):
    return self._call_code

  @classmethod
  def GetByCallCode(self, call_code):
    return self._by_call_code.get(call_code)

  def AddEnemies(self, dates):
    if random.random() < 0.1:
      self._enemies.update(random.sample(
          [d for d in dates if d is not self],
          random.randint(2, 8)))

  def GetAndSayAnswer(self, host, dates, time_index, quiet=False):
    # Copy all incoming details to an _InvitationAndResponse.
    resp = _InvitationAndResponse(host, dates, time_index, quiet)
    resp.details.update({
      'name': self._name,
      'host': host.GetName(),
    })
    if self.host:
      resp.details['old_host'] = self.host.GetName()
    resp.filtered_history = [
        c for c in self._call_history
        if c.host_name == resp.host.GetName()]
    logging.debug(
        'call from %s at t=%.2f', resp.host.GetName(), resp.time_index)
    logging.debug('got %d calls from you before', len(resp.filtered_history))

    # Run the decision-making process (which stops as soon as we've a response).
    self._CheckPolice(resp)
    self._CheckEnemies(resp)
    special_conditions = [
        self._CheckCallBack,
        self._CheckAnnoyed,
        self._CheckAlreadyAtParty]
    random.shuffle(special_conditions)
    for special_check_fn in special_conditions:
      special_check_fn(resp)
    self._DecideAmongEntryConditions(resp)

    # Record the response, say it, and return the external details.
    self._call_history.append(_CallRecord(
        resp.is_coming, resp.response, resp.host.GetName(), resp.time_index))
    self._Say(
      self._GetMessageTemplate(resp.response) % resp.details,
      resp.response is _RESPONSES.NO_CHORE,
      resp.quiet)
    return resp.is_coming, resp.friend

  @_NoopIfHasResponse
  def _CheckEnemies(self, resp):
    enemies = resp.host.CheckDates(self._enemies)
    enemy = random.choice(list(enemies)) if enemies else None
    if enemy:
      resp.response = _RESPONSES.NO_ENEMY
      resp.is_coming = False
      resp.details['enemy'] = enemy.GetName()
    else:
      logging.debug('no enemies at the party (I have %d)', len(self._enemies))

  @_NoopIfHasResponse
  def _CheckPolice(self, resp):
    if ((resp.host in self._blacklist and random.random() < 0.7)
        or (any(record.response in (_RESPONSES.NO_ANNOYED, _RESPONSES.NO_POLICE)
                for record in resp.filtered_history)
            and random.random() < 0.95)):
      resp.response = _RESPONSES.NO_POLICE
      resp.is_coming = False
      self._blacklist.add(resp.host)

  @_NoopIfHasResponse
  def _CheckCallBack(self, resp):
    if not resp.filtered_history:
      return
    prev_call = resp.filtered_history[-1]
    if prev_call.response == _RESPONSES.NO_CHORE_TRY_AGAIN:
      if (resp.time_index - prev_call.time_index) < 2.0:
        logging.debug('asked you to call be back recently, likely to come')
        if random.random() < (0.65 if self.host else 0.99):
          resp.is_coming = True
          resp.response = _RESPONSES.YES_CALLBACK
      else:
        logging.debug('asked you to call be back so long ago, feel miffed')
        r = random.random()
        if r < 0.1:
          resp.is_coming = True
          resp.response = _RESPONSES.YES_CALLBACK
        elif r < 0.9:
          resp.is_coming = False
          resp.response = _RESPONSES.NO_ANNOYED

  @_NoopIfHasResponse
  def _CheckAnnoyed(self, resp):
    forget_rounds = 3.0
    for num_recent_nos, record in enumerate(self._call_history[::-1]):
      if (record.is_coming
          or (resp.time_index - record.time_index) >= forget_rounds):
        break
    else:
      num_recent_nos = 0
    logging.debug('rejected %d most recent callers', num_recent_nos)

    if num_recent_nos >= 3:
      if random.random() < 0.9:
        resp.is_coming = False
        resp.response = _RESPONSES.NO_ANNOYED
    if resp.filtered_history:
      prev_call = resp.filtered_history[-1]
      logging.debug('you called me before')
      if (resp.time_index - prev_call.time_index) < forget_rounds:
        logging.debug('\tand that was pretty recently')
        rejection_reasons = (
            _RESPONSES.NO_CHORE,
            _RESPONSES.NO_PARTY,
            _RESPONSES.NO_ANNOYED,
            _RESPONSES.NO_POLICE)
        if ((prev_call.response in (_RESPONSES.NO_ANNOYED, _RESPONSES.NO_POLICE)
             and random.random() < 0.9)
            or (prev_call.response in rejection_reasons
                and random.random() < 0.5)):
          resp.is_coming = False
          resp.response = _RESPONSES.NO_ANNOYED
      else:
        logging.debug('\tbut it was pretty long ago')

  @_NoopIfHasResponse
  def _CheckAlreadyAtParty(self, resp):
    if not self.host:
      return

    logging.debug('already at a party')
    if self.host.GetName() == resp.host.GetName():
      logging.debug('already at your party, usually extra call is annoying')
      if random.random() < 0.8:
        resp.is_coming = False
        resp.response = _RESPONSES.NO_ANNOYED
      else:
        resp.is_coming = True
        resp.response = _RESPONSES.YES
    elif random.random() < 0.3:
      resp.is_coming = True
      if random.getrandbits(1) == 0:
        resp.response = _RESPONSES.YES_SWITCH
      else:
        resp.response = _RESPONSES.YES_SWITCH_FRIEND
        resp.friend = self._PickFriend(resp.dates, resp.host.GetName())
        resp.details['friend'] = resp.friend.GetName()
    else:
      resp.response = _RESPONSES.NO_PARTY
      resp.is_coming = False

  @_NoopIfHasResponse
  def _DecideAmongEntryConditions(self, resp):
    logging.debug('no special conditions, just deciding whether to come')
    if random.random() < 0.6:
      resp.is_coming = False
      resp.response = random.choice((
          _RESPONSES.NO_BUSY,
          _RESPONSES.NO_CHORE,
          _RESPONSES.NO_CHORE_TRY_AGAIN))
    else:
      resp.is_coming = True
      if random.random() < 0.2:
        resp.response = _RESPONSES.YES_FRIEND
        resp.friend = self._PickFriend(resp.dates, resp.host.GetName())
        resp.details['friend'] = resp.friend.GetName()
      else:
        resp.response = _RESPONSES.YES

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
    logging.log(
        logging.INFO if quiet else logging.DEBUG, '%s: %s', speaker, msg)
    if not quiet:
      voice.Say(msg, voice=speaker)

  def __str__(self):
    if not self._call_history:
      if logging.getLogger().level <= logging.DEBUG:
        return '(%s%s)' % (
            self._name,
            (' %d enemies' % len(self._enemies)) if self._enemies else '')
      else:
        return '?'
    return '%s%s' % (
        self._name,
        (' partying with %s' % self.host.GetName()) if self.host else '')


class _CustomMessageDate(Date):

  def __init__(self, voice_name, number, message_overrides, **kwargs):
    Date.__init__(self, voice_name, number, **kwargs)
    self._messages = message_overrides

  def _GetMessageTemplate(self, response):
    return random.choice(self._messages.get(response, _MESSAGES[response]))


_HYSTERICAL_MESSAGES = {
  _RESPONSES.YES: ('Yes!', 'Great.', 'OK.'),
  _RESPONSES.YES_FRIEND: (
      "Super. I'll bring %(friend)s.",
      "Sweet. I'll bring %(friend)s."),
  _RESPONSES.NO_CHORE: (
      '%(name)s is learning to twitter like a bird.',
      'Can you believe %(name)s is hissing and fizzing like a snake?'),
  _RESPONSES.NO_CHORE_TRY_AGAIN: (
      "I can't. Call me back.",
      'Not now. Try tomorrow.'),
  _RESPONSES.NO_PARTY: ('No. %(old_host)s called first.',),
  _RESPONSES.NO_BUSY: ("I can't.",),
  _RESPONSES.NO_ANNOYED: (
      "I told you I can't.",
      "%(host)s you know I can't."),
  _RESPONSES.NO_POLICE: ('You scare me.',),
  _RESPONSES.NO_ENEMY: ('Not with %(enemy)s.',),
}
_HYSTERICAL_MESSAGES[_RESPONSES.YES_CALLBACK] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES]
_HYSTERICAL_MESSAGES[_RESPONSES.YES_SWITCH] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES]
_HYSTERICAL_MESSAGES[_RESPONSES.YES_SWITCH_FRIEND] = _HYSTERICAL_MESSAGES[
    _RESPONSES.YES_FRIEND]


_GOOD_NEWS_MESSAGES = {
  _RESPONSES.YES: (
    'Congratulations you just won the sweepstakes.',
    'A lovely idea see you without fail.',
    'Oh kindest %(host)s. I will come.',
    "My goodness I'll be there."),
  _RESPONSES.YES_FRIEND: (
    "My goodness I'll be there, %(friend)s's coming too.",
    "My goodness I'll be there, my friend's coming too."),
  _RESPONSES.YES_CALLBACK: (
    "A pleasure to hear your trilling voice again so happy to tell you I'll "
    "see you my friend.",),
  _RESPONSES.YES_SWITCH: (
    'Hallelujah savior snared I am no more, your invite squashed obligation '
    'from before.',),
  _RESPONSES.YES_SWITCH_FRIEND: (
    'Accept my. New preference. Too shall come. %(friend)s.',),
  _RESPONSES.NO_CHORE_TRY_AGAIN: (
    'Whiling away hours I vacuum up frogs, if you call be back though maybe.',),
  _RESPONSES.NO_PARTY: (
    'Sad is my soft heart that I already said yes to someone: %(old_host)s.',),
  _RESPONSES.NO_BUSY: (
    'Oh kindest %(host)s. I cannot.',),
  _RESPONSES.NO_ANNOYED: (
    "You bring again distress to my worn out phone, it bothers me nonstop why"
    " haven't you learned?",
    (10 * '%(name)s ') + 'is me.',
    11 * '%(host)s '),
  _RESPONSES.NO_ENEMY: (
    'Kryptonite thy name is. %(enemy)s %(enemy)s.',),
}


_BELLS_MESSAGES = {
  _RESPONSES.YES: ('See you.', 'See you %(host)s.', '%(host)s. Thank you.'),
  _RESPONSES.YES_FRIEND: ('Great for me and %(friend)s.',),
  _RESPONSES.YES_CALLBACK: ('You came through %(host)s. See you later.',),
  _RESPONSES.YES_SWITCH: (
      'I had plans but they are changing.',
      "You're an ace. So you trump. %(old_host)s."),
  _RESPONSES.YES_SWITCH_FRIEND: (
      '%(friend)s convinced me. We will come to you.',),
  _RESPONSES.NO_CHORE_TRY_AGAIN: ('Later on I will know more.',),
  _RESPONSES.NO_PARTY: ('Got a call from %(old_host)s first.',),
  _RESPONSES.NO_BUSY: ('I am busy sad to say.', 'All. The. Chores.'),
  _RESPONSES.NO_ANNOYED: (
      'La la la. La la la.',
      'Nothing gets my goat like phone calls.'),
  _RESPONSES.NO_ANNOYED: ("Call the police it's abuse now.",),
  _RESPONSES.NO_ENEMY: ('I will catch my death from %(enemy)s.',),
}


def _GenerateCallCodes():
  """Generates 4-digit phone numbers as strings, used to call the dates."""
  all_permutations = list(itertools.permutations(range(10), 4))
  random.shuffle(all_permutations)
  for four_digits in all_permutations:
    yield ''.join(map(str, four_digits))


def MakeDates(**kwargs):
  dates = []
  custom_voices = set()
  call_codes = _GenerateCallCodes()
  for voice_name, overrides in (
      # TODO: Custom messages for Bad News.
      ('Hysterical', _HYSTERICAL_MESSAGES),
      ('Cellos', _GOOD_NEWS_MESSAGES),  # TODO: Custom messages for Cellos.
      ('Pipe Organ', _GOOD_NEWS_MESSAGES),  # TODO: Custom messages for P.O.
      ('Good News', _GOOD_NEWS_MESSAGES),
      ('Bells', _BELLS_MESSAGES)):
    if voice_name in voice.VOICES_SET:
      dates.append(_CustomMessageDate(voice_name, call_codes.next(), overrides))
      custom_voices.add(voice_name)
  dates += [Date(v, call_codes.next(), **kwargs)
            for v in (voice.VOICES_SET - custom_voices)]
  random.shuffle(dates)
  return dates
