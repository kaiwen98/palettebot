class Singleton(type):
  def __init__(self, name, bases, mmbs):
        print(self)
        print(name)
        super(Singleton, self).__init__(name, bases, mmbs)
        self._instance = super(Singleton, self).__call__()

  def __call__(self, *args, **kw):
      return self._instance