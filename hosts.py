class Host:
  def __init__(self, name):
    self.name = name
    self.dates = set()

  def GetName(self):
    return self.name

  def GetNumDates(self):
    return len(self.dates)

  def Rsvp(self, date, is_coming):
    if is_coming:
      if date.host:
        date.host.Rsvp(date, False)
      date.host = self
      self.dates.add(date)
    else:
      if date in self.dates:
        self.dates.remove(date)
        date.host = None
