import logging
import random
import subprocess


__output = subprocess.check_output(['say', '-v', '?'])
VOICES = [line.split()[0] for line in __output.split('\n') if line]
VOICES_SET = frozenset(VOICES)


def GetRandomVoice():
  return random.choice(VOICES)


DEFAULT_VOICE = GetRandomVoice()


def Say(message, voice=DEFAULT_VOICE):
  if voice not in VOICES:
    raise ValueError(
        'voice %r not valid, should be one of %s' % (voice, VOICES))
  subprocess.check_call(['say', '-v', voice, message])
