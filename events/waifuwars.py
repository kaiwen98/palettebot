"""
Consolidates all commands that is related to Inktober.
"""
import asyncio
import os
import discord
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile


import config_loader as cfg
from models.DiscordBot import DiscordBot
from controller.gdrive_uploader import upload_to_gdrive
import asyncio
import pandas as pd
from discord.ext import commands

from controller.commons import get_list_of_artists
from controller.inktober import DICT_DAY_TO_PROMPT
from controller.waifuwars import update_waifuwars
from controller import waifuwars as waf
from utils.constants import (
    APPROVE_SIGN,
    DIR_OUTPUT, 
    DISCORD_CHANNEL_ART_GALLERY, 
    DISCORD_MESSAGES_LIMIT,
    NOT_APPROVE_SIGN,
    WAIFUWARS_APPROVE_CHANNEL,
    WAIFUWARS_CONCEDE_SIGN
)
from utils.utils import (
    calculate_score, 
    clear_folder,
    get_day_from_message,
    get_num_days_away, 
    get_rank_emoji, 
    get_timestamp_from_curr_datetime, 
    get_today_date,
    remove_messages
)

import config_loader as cfg


def register_events():
  bot = DiscordBot().bot
  @bot.command(
    name='waf_getscores', 
    help='Get Drawtober scores'
  )
  async def waf_get_scores_(ctx):
    print("here")
    await waf.get_scores(True)

  @bot.command(
      name='ww_getscores', 
      help='Get Drawtober scores'
  )
  async def get_scores_(ctx):
      print("here")
      await waf.get_scores(True)
      

  @bot.event
  async def on_raw_reaction_add_waifuwars(payload, approve_queue):
      message_approve_artwork_id = payload.message_id
      user = payload.member
      emoji = payload.emoji.name
      print(emoji)
      guild = DiscordBot().get_guild(None)
      message_approve_artwork = await DiscordBot().get_channel(guild, WAIFUWARS_APPROVE_CHANNEL).fetch_message(message_approve_artwork_id)
      # print(message.id, type(message.id), list(approve_queue.keys()))

      if message_approve_artwork.id not in [i["message_approve_artwork"].id for i in approve_queue]:
          print(1)
          return

      # specifies the channel restriction
      if user.name not in ["okai_iwen", "tako", "Hoipus", approve_queue[-1]["attacked_user"].name]:
          print(2)
          return 

      if message_approve_artwork.channel.name != os.getenv(WAIFUWARS_APPROVE_CHANNEL):
          print(3)
          return

      approve_request_to_service = tuple(filter(lambda i: i["message_approve_artwork"].id == message_approve_artwork.id, approve_queue))[0]
      #print(approve_request_to_service)
      attacking_user, attacked_user = approve_request_to_service["attacking_user"], approve_request_to_service["attacked_user"]
      message_artwork = approve_request_to_service["message_artwork"]
      approve_queue.remove(approve_request_to_service)

      #print(approve_queue)

      if emoji == WAIFUWARS_CONCEDE_SIGN:
          await DiscordBot().get_channel(guild, os.getenv(WAIFUWARS_APPROVE_CHANNEL)).send(
                      "**<@%s> conceded to this post!**:flag_white: :flag_white: :flag_white: \n**<@%s> won a WAIFU & HUSBANDO  WAR round! **:trophy: \n%s" % (user.id, message_artwork.author.id, message_artwork.jump_url),
                  )
          await update_waifuwars(attacked_user, attacking_user, approve_request_to_service)

      await remove_messages([message_approve_artwork])



