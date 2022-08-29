
"""
Consolidates all commands that is related to the birthdayTracker.
"""
from discord.utils import get
from models.DiscordBot import DiscordBot
from controller import inktober as ink
import discord
import asyncio
from controller.excelHandler import (
  MEMBER_INFO_BIRTHDAY_STATE,
  MEMBER_INFO_COL_BDATE,
  MEMBER_INFO_COL_DISCORD,
  get_fuzzily_discord_handle,
  set_up_member_info,
  update_birthday_state_to_gsheets
)

from utils.commons import EXTRAVAGANZA_ROLE, MEMBER_ROLE
from utils.utils import (
  find_invite_by_code,
  get_msg_by_jump_url,
  get_day_from_message,
  get_num_days_away
)

import datetime

import pandas as pd

import config_loader as cfg

"""
    This code is referenced from https://medium.com/@tonite/finding-the-invite-code-a-user-used-to-join-your-discord-server-using-discord-py-5e3734b8f21f

    Applied for Extravaganza 2022; allow participants to join the Discord Server to attend lessons.
    The special invite code is https://discord.gg/ddekPqAckv.
"""

def register_events():
  bot = DiscordBot().bot
  @bot.event
  async def on_member_remove(member):

    # Updates the cache when a user leaves to make sure
    # everything is up to date

    DiscordBot().invite_links[member.guild.id] = await member.guild.invites()

  @bot.event
  async def on_member_join(member):
    global EXTRAVAGANZA_INVITE_LINK 
    # Getting the invites before the user joining
    # from our cache for this specific guild

    invites_before_join = DiscordBot().invite_links[member.guild.id]
    print("--before ", DiscordBot().invite_links[member.guild.id])
    # Getting the invites after the user joining
    # so we can compare it with the first one, and
    # see which invite uses number increased

    invites_after_join = await member.guild.invites()
    print("--after ", DiscordBot().invite_links[member.guild.id])

    # Loops for each invite we have for the guild
    # the user joined.

    for invite in invites_before_join:

      # Now, we're using the function we created just
      # before to check which invite count is bigger
      # than it was before the user joined.
      print(invite.uses)

      print(find_invite_by_code(invites_after_join, invite.code).uses)
      if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:

        # Now that we found which link was used,
        # we will print a couple things in our console:
        # the name, invite code used the the person
        # who created the invite code, or the inviter.

        print(f"Member {member.name} Joined")
        print(f"Invite Code: {invite.code}")
        print(f"Inviter: {invite.inviter}")

        # We will now update our cache so it's ready
        # for the next user that joins the guild

        DiscordBot().invite_links[member.guild.id] = invites_after_join

        # We return here since we already found which 
        # one was used and there is no point in
        # looping when we already got what we wanted

        print(EXTRAVAGANZA_INVITE_LINK)
        if invite.code == EXTRAVAGANZA_INVITE_LINK:
          role = get(member.guild.roles, name=EXTRAVAGANZA_ROLE)
          await member.add_roles(role)
        else:
          role = get(member.guild.roles, name=MEMBER_ROLE)
          await member.add_roles(role)
          return

