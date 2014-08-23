class Host:
  def __init__(self, name):
    self._name = name
    self.ClearDates()

  def GetName(self):
    return self._name

  def GetNumDates(self):
    return len(self._dates)

  def ClearDates(self):
    self._dates = set()

  def Rsvp(self, date, is_coming, time_index):
    if is_coming:
      if date.host:
        date.host.Rsvp(date, False, time_index)
      date.host = self
      date.rsvp_time = time_index
      self._dates.add(date)
    else:
      if date in self._dates:
        self._dates.remove(date)
        date.host = None
        date.rsvp_time = time_index

  def CheckDates(self, check_set):
    return self._dates.intersection(check_set)

  def GetDateNames(self):
    return [d.GetName() for d in self._dates]
