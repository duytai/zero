class GlobalName:
  _instance = None
  counter = 0

  def __new__(cls):
    if not cls._instance:
      cls._instance = super(GlobalName, cls).__new__(cls)
    return cls._instance

  def names(self):
    while True:
      self.counter += 1
      yield f'tmp_{self.counter}'

gn = GlobalName()