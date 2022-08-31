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
from utils.commons import DISCORD_GUILD

from utils.utils import (
  get_day_from_message,
  get_num_days_away
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
    await channel.send(
      "```Delay Change Complete!```"
    )

  @bot.command(
    name='bd_listmonth', 
    help='Get all birthdays for the month'
  )
  async def get_month_birthdays(ctx):
    output = []
    member_info = set_up_member_info()
    guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
    channel = DiscordBot().get_channel(guild, "bot-spam")
    df_discord_members = pd.DataFrame({
      "Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
      "uid" : [i.id for i in guild.members],
    })
    for index, row in member_info.iterrows():
      try:

        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members) is None:
          continue

        if row[MEMBER_INFO_COL_BDATE].date().month == (datetime.datetime.now() + datetime.timedelta(hours = 8)).date().month:
          output.append("%s | %s | %s\n " % (
            # Discord name
            get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members), 
            # Month and date
            datetime.datetime.strftime(row[MEMBER_INFO_COL_BDATE], "%m-%d"),
            # Number of days away
            get_num_days_away(row[MEMBER_INFO_COL_BDATE].date())
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
    member_info[MEMBER_INFO_BIRTHDAY_STATE] = [STATE_NO_SHOUTOUTS for i in range(member_info.shape[0])]
    await channel.send(
      "```The Bot has forgotten when shoutouts were made!```"
    )
    update_birthday_state_to_gsheets(member_info)


