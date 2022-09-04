"""
Consolidates all commands that is related to Inktober.
"""
from models.DiscordBot import DiscordBot
from controller import weeklyprompts as weekp
import asyncio
from utils.constants import INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL
from utils.utils import (
  get_day_from_message
)

def register_events():

  bot = DiscordBot().bot

  @bot.command(
    name='weekp_getscores', 
    help='Get Weekly Prompts scores'
  )

  async def weekp_get_scores_(ctx):
    await weekp.get_scores(True)
