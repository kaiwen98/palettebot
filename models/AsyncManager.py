import asyncio
from models.Singleton import Singleton

class AsyncManager(metaclass=Singleton):
  def __init__(self):
    self.lock = asyncio.Lock()
