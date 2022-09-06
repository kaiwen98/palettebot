from controller.excelHandler import set_up_member_info
from models.DiscordBot import DiscordBot
import pandas as pd

import code
import os
import discord
from discord.ext import commands
from discord.utils import get
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile


import config_loader as cfg
from controller.gdrive_uploader import upload_to_gdrive
import asyncio
import pandas as pd
from controller.inktober import DICT_DAY_TO_PROMPT
from controller import inktober as ink
from controller import waifuwars as waf
from config_loader import load_config
from models.DiscordBot import DiscordBot

from controller.excelHandler import (
  get_fuzzily_discord_handle, 
  pretty_print_social_handle_wrapper,
  set_up_inktober,
  set_up_member_info, 
  set_up_palette_particulars_csv,
  update_birthday_state_to_gsheets,
  update_inktober_state_to_gsheets, 
  verify_is_okay_to_share_by_discord_name
)
from controller.commons import get_list_of_artists
from utils.config_utils import is_done_this_day
from utils.constants import (
  BIRTHDAY_REPORT_CHANNEL,
  DEFAULT_COLUMN_DATA,
  DELAY,
  DIR_OUTPUT, 
  DISCORD_CHANNEL_ART_GALLERY,
  DISCORD_GUILD, 
  DISCORD_MESSAGES_LIMIT,
  EXTRAVAGANZA_ROLE,
  GSHEET_BIRTHDAY_COLUMN_STATE,
  GSHEET_COLUMN_BIRTHDAY,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_DISCORD_ID,
  HOUR_WISH_BIRTHDAY,
  MEMBER_ROLE,
  PATH_IMG_BIRTHDAY,
  PATH_IMG_BIRTHDAY_1WEEK,
  STATE_NO_SHOUTOUTS,
  STATE_SHOUTOUT_DAY,
  STATE_SHOUTOUT_WEEK
)
from utils.utils import (
  get_num_days_away, 
  get_rank_emoji, 
  get_timestamp_from_curr_datetime, 
  get_today_date,
  get_today_datetime, 
  remove_messages
)
import pandas as pd

async def task():
  """
  Entry point to birthday logic. 
        TODO: Relocate this code to controller/birthday.py 
  """
  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  channel = DiscordBot().get_channel(guild, os.getenv(BIRTHDAY_REPORT_CHANNEL))

  print("[BDAY] Starting Birthday Applet...")
  while True:
    await asyncio.sleep(int(os.getenv(DELAY)) + 10)

    if is_done_this_day(hour=HOUR_WISH_BIRTHDAY): 
      continue
    # try:
    await handle_check_birthdates_and_give_shoutout()
    # except Exception as e:
    #     await channel.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )


async def handle_check_birthdates_and_give_shoutout():
  """
  The code should handle birthday logic.

  """
  has_sent_bday_pic = False
  has_sent_week_pic = False
  is_changed = False



  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))


  channel = DiscordBot().get_channel(guild, os.getenv(BIRTHDAY_REPORT_CHANNEL))

  for player in DiscordBot().players.values():
    birthday = player[GSHEET_COLUMN_BIRTHDAY]
    if pd.isnull(birthday):
      continue

    try:
      if get_num_days_away(birthday.date()) == 0 and \
          (player[GSHEET_BIRTHDAY_COLUMN_STATE] != STATE_SHOUTOUT_DAY):

        # Birthday is today,
        if has_sent_bday_pic is False:
          await channel.send(
            file = discord.File(PATH_IMG_BIRTHDAY)
          )  

          has_sent_bday_pic = True

          await channel.send(
            "Birthday baby sighted! :mag_right: :mag_right: HAPPY BIRTHDAY <@%s> :birthday: :candle: :birthday: :candle:" % \
            (player[GSHEET_COLUMN_DISCORD_ID]),
          )  

          player[GSHEET_BIRTHDAY_COLUMN_STATE] = STATE_SHOUTOUT_DAY

        elif get_num_days_away(birthday.date()) <= 7 and \
          get_num_days_away(birthday.date()) > 0 and \
          (player[GSHEET_BIRTHDAY_COLUMN_STATE] != STATE_SHOUTOUT_WEEK):
          # Birthday is a week away,

          if has_sent_week_pic is False:
            await channel.send(
              file = discord.File(PATH_IMG_BIRTHDAY_1WEEK)
            )  
            has_sent_week_pic = True

            await channel.send(
              "<@%s> 's birthday is less than a week away! Are yall excited :))) :eyes: :eyes: :eyes:" % \
              (player[GSHEET_COLUMN_DISCORD_ID]),
            )  
            player[GSHEET_BIRTHDAY_COLUMN_STATE] = STATE_SHOUTOUT_WEEK

        elif datetime.now().day == 1 and datetime.now().month == 1:
          # Reset
          player[GSHEET_BIRTHDAY_COLUMN_STATE] = STATE_NO_SHOUTOUTS    

    except:
      print("Date not valid.")

    await DiscordBot().update_players_to_db()
