import asyncio
from models.Singleton import Singleton

class AsyncManager(metaclass=Singleton):
  def __init__(self, *args, **kw):
    self.lock = asyncio.Lock()
