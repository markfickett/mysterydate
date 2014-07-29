class Host:
  def __init__(self, name):
    self._name = name
    self._dates = set()

  def GetName(self):
    return self._name

  def GetNumDates(self):
    return len(self._dates)

  def Rsvp(self, date, is_coming):
    if is_coming:
      if date.host:
        date.host.Rsvp(date, False)
      date.host = self
      self._dates.add(date)
    else:
      if date in self._dates:
        self._dates.remove(date)
        date.host = None
