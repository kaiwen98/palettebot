"""
Consolidates all commands that is related to the birthdayTracker.
"""
import controller
from controller.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from controller.birthdayTracker import birthday_task
from controller.commons import (
  get_photos,
  get_all_members_text
)
from controller.excelHandler import (
  MEMBER_INFO_BIRTHDAY_STATE,
  MEMBER_INFO_COL_BDATE,
  MEMBER_INFO_COL_DISCORD,
  STATE_NO_SHOUTOUTS,
  get_fuzzily_discord_handle,
  set_up_member_info,
  set_up_palette_particulars_csv,
  update_birthday_state_to_gsheets
)

import controller.excelHandler as exc
from config_loader import (
  ART_FIGHT_MODE_INKTOBER,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_STATE,
  INKTOBER_APPROVE_CHANNEL,
  INKTOBER_RECEIVE_CHANNEL,
  GUILD
)
from utils.commons import EXTRAVAGANZA_ROLE
from utils.utils import (
  find_invite_by_code,
  get_msg_by_jump_url,
  get_day_from_message,
  get_num_days_away,
)

import datetime

import pandas as pd

import config_loader as cfg

bot = DiscordBot().bot

def register_events():
  @bot.event
  async def on_ready():
    for guild in bot.guilds:
      print(guild)
      if guild.name == GUILD:
        break

      # Getting all the guilds our bot is in
      for guild in bot.guilds:

        # Adding each guild's invites to our dict
        DiscordBot().invite_links[guild.id] = await guild.invites()
        print("--begin ", DiscordBot().invite_links[guild.id])

      print(guild.roles)

      print(f'{bot.user} has connected to Discord!')
      if os.getenv("ENV") == "production":
        bot.loop.create_task(birthday_task())
      if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
        bot.loop.create_task(ink.inktober_task())
      elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
        bot.loop.create_task(waf.waifuwars_task())


  @bot.command(
    name='export', 
    help='Provide \"export DD MM DD MM YYYY\", with start date first and end date last. The year is optional, so no entry means current year.'
  )
  async def export(ctx, channel: str, dd_begin: int, mm_begin: int, dd_end: int, mm_end: int, year=None):
    global df

    print(",", year, ",")

    if year is None:
      year = datetime.datetime.today().year

      palette_particulars = set_up_palette_particulars_csv()
      await ctx.send(
        "```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
      )
      try:
        await get_photos(channel, palette_particulars, dd_begin, mm_begin, dd_end, mm_end, year, ctx)
      except Exception as e:
        await ctx.send(
          "```Error occured! Contact the administrator. Message: %s```" % (str(e))
        )

  @bot.command(
    name='getallmembers', 
    help='Provide \"getallmembers VOICECHANNEL\", Outputs a list of members in a specified voice chat.'
  )
  async def get_all_members(ctx, channel: str):
    palette_particulars = set_up_palette_particulars_csv()
    await ctx.send(
      "```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
    )
    try:
      await get_all_members_text(channel, ctx)
    except Exception as e:
      await ctx.send(
        "```Error occured! Contact the administrator. Message: %s```" % (str(e))
      )

  @bot.command(
    name='ex2022_kick_participants', 
    help='Kick all participants with the role: Extravaganza 2022 Participant'
  )
  async def ex2020_kick_participants(ctx):
    guild = DiscordBot().get_guild(GUILD)
    for member in guild.members:
      if member.roles[1].name == EXTRAVAGANZA_ROLE:
        await guild.kick(member, reason = "Thank you for joining Extravaganza 2022! Hope it has been fun for you :)") 

  @bot.command(
    name='ex2022_set_new_invite', 
    help='Set a new invite link. If no link is provided, a new one is generated.'
  )
  async def ex2020_set_new_invite(ctx, updated_invite = None):
    guild = DiscordBot().get_guild(GUILD)
    link = None
    invites = await guild.invites()

    if updated_invite is None:
      channel = await DiscordBot().get_channel(guild, "general")
      link = channel.create_invite()
      link = link.code

    else:
      for i in invites:
        if i.code == updated_invite:
          link = i.code
          break

      if link is not None:
        await ctx.send(
          "```Your updated invite link is https://discord.gg/%s```" % (link)
        )

        if DiscordBot().extravaganza_invite_link is not None:

          tmp = find_invite_by_code(invites, DiscordBot().extravaganza_invite_link)
          if tmp is not None:
            await tmp.delete()

          DiscordBot().extravaganza_invite_link = link
          print(DiscordBot().extravaganza_invite_link, " is created")

      else:
        await ctx.send(
          "```We cannot find the link. It is invalid.```"
        )    

      DiscordBot().invite_links[guild.id] = await guild.invites()
