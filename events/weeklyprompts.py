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
import json
import re

def register_events():

  bot = DiscordBot().bot

  @bot.command(
    name='weekp_get_scores', 
    help='Get Weekly Prompts scores'
  )

  async def weekp_get_scores(ctx):
    await weekp.get_scores(True)

  @bot.command(
    name='weekp_credit_score', 
    help='weekp_credit_score <week> <score> to edit score for the week. You can use negative values to minus score'
  )

  async def weekp_credit_score(ctx, discord_id, week, score):
    discord_id = re.sub(r'[@<>]', '', discord_id)
    print(discord_id)
    player = DiscordBot().players[discord_id]
    player.increment_weeklyprompt_score_at_week(int(week), int(score))
    await ctx.send(json.dumps(player.weeklyprompts_week_to_num_submitted_artworks))
    #await weekp.get_scores(True)
