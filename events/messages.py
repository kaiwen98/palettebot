"""
Consolidates all commands that is related to the birthdayTracker.
"""
from controller.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from controller.birthdayTracker import birthday_task
from controller import waifuwars as waf
from controller.excelHandler import (
  MEMBER_INFO_BIRTHDAY_STATE,
  MEMBER_INFO_COL_BDATE,
  MEMBER_INFO_COL_DISCORD,
  STATE_NO_SHOUTOUTS,
  get_fuzzily_discord_handle,
  set_up_member_info,
  update_birthday_state_to_gsheets
)
from config_loader import (
  ART_FIGHT_MODE_INKTOBER,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_STATE,
  INKTOBER_APPROVE_CHANNEL,
  INKTOBER_RECEIVE_CHANNEL,
  GUILD
)
from utils.utils import (
  find_invite_by_code,
  get_msg_by_jump_url,
  get_day_from_message,
  get_num_days_away
)

import datetime
import os
import pandas as pd

import config_loader as cfg
from controller.DiscordBot import DiscordBot

bot = DiscordBot().bot

def register_events():
  @bot.event
  async def on_message(message):
    if message.channel.name == "bot-spam":
      await bot.process_commands(message)
      return 
    if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
      await ink.on_message_inktober(message, DiscordBot().approve_queue)
    elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
      await waf.on_message_waifuwars(message, DiscordBot().approve_queue)

  @bot.event
  async def on_raw_reaction_add(payload):
    if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
      await ink.on_raw_reaction_add_inktober(payload, DiscordBot().approve_queue)
    elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
      await waf.on_raw_reaction_add_waifuwars(payload, DiscordBot().approve_queue)

