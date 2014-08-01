import logging
import random
import subprocess


class _VoiceSummary:
  def __init__(self, summary_line):
    voice_info, self.message = summary_line.split('#')
    self.voice = ' '.join(voice_info.split()[:-1])


__output = subprocess.check_output(['say', '-v', '?'])
VOICES = [
    _VoiceSummary(summary_line).voice
    for summary_line in __output.split('\n') if summary_line]
VOICES_SET = frozenset(VOICES)
RATE_WPM = '300'


def GetRandomVoice(exclude=None):
  if exclude:
    return random.choice(list(VOICES_SET - set((exclude,))))
  else:
    return random.choice(VOICES)


DEFAULT_VOICE = GetRandomVoice()


def Say(message, voice=DEFAULT_VOICE, rate_wpm=RATE_WPM):
  if voice not in VOICES:
    raise ValueError(
        'voice %r not valid, should be one of %s' % (voice, VOICES))
  subprocess.check_call(['say', '-v', voice, '-r', str(rate_wpm), message])


def SayAllSamples():
  """Speaks a line of sample text in each available voice."""
  summary = subprocess.check_output(['say', '-v', '?'])
  for summary_line in summary.split('\n'):
    if not summary_line:
      continue
    info = _VoiceSummary(summary_line)
    logging.info('%s: %s', info.voice, info.message)
    Say(info.message, voice=info.voice, rate_wpm=500)
