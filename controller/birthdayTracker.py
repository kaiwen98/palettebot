from config_loader import (
  BIRTHDAY_REPORT_CHANNEL,
  GUILD,
  DELAY
)
from controller.excelHandler import set_up_member_info
from controller.DiscordBot import DiscordBot
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
from controller.DiscordBot import DiscordBot

from controller.excelHandler import (
  INKTOBER_STATE,
  MEMBER_INFO_BIRTHDAY_STATE,
  MEMBER_INFO_COL_BDATE,
  MEMBER_INFO_COL_DISCORD,
  STATE_APPROVED,
  STATE_NO_SHOUTOUTS,
  STATE_SHOUTOUT_DAY,
  STATE_SHOUTOUT_WEEK,
  STATE_UNDER_APPROVAL,
  get_fuzzily_discord_handle, 
  pretty_print_social_handle_wrapper,
  set_up_inktober,
  set_up_member_info, 
  set_up_palette_particulars_csv,
  update_birthday_state_to_gsheets,
  update_birthday_state_to_local_disk,
  update_inktober_state_to_gsheets, 
  verify_is_okay_to_share_by_discord_name
)
from controller.commons import get_list_of_artists
from utils.commons import (
  DIR_OUTPUT, 
  DISCORD_CHANNEL_ART_GALLERY,
  DISCORD_GUILD, 
  DISCORD_MESSAGES_LIMIT,
  EXTRAVAGANZA_ROLE,
  MEMBER_ROLE,
  PATH_IMG_BIRTHDAY,
  PATH_IMG_BIRTHDAY_1WEEK
)
from utils.utils import (
  get_num_days_away, 
  get_rank_emoji, 
  get_timestamp_from_curr_datetime, 
  get_today_date, 
  remove_messages
)

async def birthday_task():
  """
  Entry point to birthday logic. 
        TODO: Relocate this code to controller/birthday.py 
  """
  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  channel = DiscordBot().get_channel(guild, "bot-spam")
  while True:
    # try:
    await handle_check_birthdates_and_give_shoutout()
    # except Exception as e:
    #     await channel.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )

    await asyncio.sleep(int(os.getenv(DELAY)))

async def handle_check_birthdates_and_give_shoutout():
  """
  The code should handle birthday logic.

  """
  has_sent_bday_pic = False
  has_sent_week_pic = False
  member_info = set_up_member_info()

  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))

  df_discord_members = pd.DataFrame({
    "Discord": [member.name + "#" + str(member.discriminator) for member in guild.members],
    "uid" : [member.id for member in guild.members],
  })

  print(df_discord_members)

  channel = DiscordBot().get_channel(guild, os.getenv(BIRTHDAY_REPORT_CHANNEL))

  for index, row in member_info.iterrows():
    if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members, get_uid=True) is None:
      continue

    try:
      if get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) == 0 and \
          (int(row[MEMBER_INFO_BIRTHDAY_STATE]) & STATE_SHOUTOUT_DAY == 0):
        # Birthday is today,

        if has_sent_bday_pic is False:
          await channel.send(
            file = discord.File(PATH_IMG_BIRTHDAY)
          )  

          has_sent_bday_pic = True

          await channel.send(
            "Birthday baby sighted! :mag_right: :mag_right: HAPPY BIRTHDAY <@%s> :birthday: :candle: :birthday: :candle:" % \
            (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members, get_uid=True)),
          )  

          member_info.at[index, MEMBER_INFO_BIRTHDAY_STATE] = int(row[MEMBER_INFO_BIRTHDAY_STATE]) | STATE_SHOUTOUT_DAY

        elif get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) <= 7 and \
          get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) > 0 and \
          (int(row[MEMBER_INFO_BIRTHDAY_STATE]) & STATE_SHOUTOUT_WEEK == 0):
          # Birthday is a week away,

          if has_sent_week_pic is False:
            await channel.send(
              file = discord.File(PATH_IMG_BIRTHDAY_1WEEK)
            )  
            has_sent_week_pic = True

            await channel.send(
              "<@%s> 's birthday is less than a week away! Are yall excited :))) :eyes: :eyes: :eyes:" % \
              (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members, get_uid=True)),
            )  
            member_info.at[index, MEMBER_INFO_BIRTHDAY_STATE] = int(row[MEMBER_INFO_BIRTHDAY_STATE]) | STATE_SHOUTOUT_WEEK

          elif datetime.now().day == 1 and datetime.now().month == 1:
            member_info[MEMBER_INFO_BIRTHDAY_STATE] = [STATE_NO_SHOUTOUTS for i in range(member_info.shape[0])]
    except:
      print("Date not valid.")

    print(member_info)
    update_birthday_state_to_gsheets(member_info)


