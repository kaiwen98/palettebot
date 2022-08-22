"""
Consolidates all commands that is related to Inktober.
"""
from controller.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from config_loader import (
  INKTOBER_APPROVE_CHANNEL,
  INKTOBER_RECEIVE_CHANNEL
)
from utils.utils import (
  get_msg_by_jump_url,
  get_day_from_message
)

import config_loader as cfg

bot = DiscordBot().bot

def register_events():
  @bot.command(
    name='waf_getscores', 
    help='Get Drawtober scores'
  )
  async def waf_get_scores_(ctx):
    print("here")
    await waf.get_scores(True)


