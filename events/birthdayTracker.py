"""
Consolidates all commands that is related to the birthdayTracker.
"""
import os
from models.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from controller.excelHandler import (
  get_fuzzily_discord_handle,
  set_up_member_info,
  update_birthday_state_to_gsheets
)
from utils.constants import DEFAULT_COLUMN_DATA, DISCORD_GUILD, GSHEET_BIRTHDAY_COLUMN_STATE, GSHEET_COLUMN_BIRTHDAY, GSHEET_COLUMN_DISCORD, STATE_NO_SHOUTOUTS

from utils.utils import (
  get_day_from_message,
  get_num_days_away,
  get_today_datetime
)

import datetime

import pandas as pd

import config_loader as cfg


def register_events():

  bot = DiscordBot().bot
  @bot.command(
    name='bd_setdelay', 
    help='Change birthday delay in seconds.'
  )
  async def change_bd_delay(ctx, delay):
    guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
    channel = DiscordBot().get_channel(guild, "bot-spam");
    DiscordBot().update_delay = delay
    await channel.send(
      "```Delay Change Complete!```"
    )

  @bot.command(
    name='bd_listmonth', 
    help='Get all birthdays for the month'
  )
  async def get_month_birthdays(ctx):
    output = []
    guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
    channel = DiscordBot().get_channel(guild, "bot-spam")
    for player in DiscordBot().players.values():
      try:
        birthday = player[GSHEET_COLUMN_BIRTHDAY]
        if pd.isnull(birthday):
          continue

        if player[GSHEET_COLUMN_BIRTHDAY].date().month == get_today_datetime().date().month:
          output.append("%s | %s | %s\n " % (
            # Discord name
            player[GSHEET_COLUMN_DISCORD], 
            # Month and date
            datetime.datetime.strftime(birthday, "%m-%d"),
            # Number of days away
            get_num_days_away(birthday)
          ))

      except Exception as e:
        output = ["Something went wrong"]
        continue

    await ctx.send(
      "```" + "".join(output) + "```"
    )

  @bot.command(
    name='bd_forgetshoutouts', 
    help='Forget who the bot has wished birthdays for.'
  )
  async def reset_shoutout_counter(ctx):
    member_info = set_up_member_info()

    guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
    channel = DiscordBot().get_channel(guild, "bot-spam")

    # reset all birthday wishing state to none
    for player in DiscordBot().players.values():
      player[GSHEET_BIRTHDAY_COLUMN_STATE] = STATE_NO_SHOUTOUTS
    await channel.send(
      "```The Bot has forgotten when shoutouts were made!```"
    )

    DiscordBot().update_players_to_db()


