"""
Consolidates all commands that is related to Inktober.
"""
from models.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from utils.commons import INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL
from utils.utils import (
  get_day_from_message
)

def register_events():

  bot = DiscordBot().bot
  @bot.command(
    name='ink_resetday', 
    help='Resets day and repeats announcement'
  )
  async def reset_day(ctx):
    async with asyncio.Lock():
      cfg.curr_day = -1
      await ctx.send(
        "```Day reset!```" 
      )

  @bot.command(
    name='ink_getscores', 
    help='Get Drawtober scores'
  )

  async def ink_get_scores_(ctx):
    await ink.get_scores(True)

  @bot.command(
    name='ink_addmsgtoapprove', 
    help='If there are some approve messages that does not react to reactions, we use this command to add them back manually into the approve list.'
  )
  async def add_msg_to_approve(ctx, link: str):

    # try:

    msg_to_approve = await DiscordBot().get_msg_by_jump_url(DiscordBot().bot, ctx, os.getenv(INKTOBER_APPROVE_CHANNEL), link.strip())   

    if msg_to_approve is None:
      return

    #call_stack.append(selected_message)
    #msg_to_approve = call_stack.pop() 
    msg_id = msg_to_approve.id

    if msg_id in map(
      lambda x: x["message_approve_artwork"],
      DiscordBot().approve_queue
    ):
      await ctx.send(
        "```Message is already in queue...```"
      )
      return

    link_to_msg_artwork = msg_to_approve.content.strip().split(" ")[-1]

    msg_artwork = await DiscordBot().get_msg_by_jump_url(ctx, os.getenv(INKTOBER_RECEIVE_CHANNEL), link_to_msg_artwork)
    day = get_day_from_message(msg_artwork)

    DiscordBot().approve_queue.append({
      "type": "inktober",
      "day": day,
      "message_artwork": msg_artwork,
      "message_approve_artwork": msg_to_approve
    })

    await ctx.send(
      "```Added %d! Approve Queue contents is now: %s```" % (msg_id, ",".join([str(i) for i in DiscordBot().approve_queue]))
    )
    # except Exception as e:
    #     await ctx.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )

