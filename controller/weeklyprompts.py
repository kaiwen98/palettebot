from datetime import datetime
import pystache
import os
from config_loader import get_recorded_week

from models.DiscordBot import DiscordBot
import discord
import pandas as pd
import requests
import asyncio
import re

from controller.excelHandler import (
  get_fuzzily_discord_handle, 
  set_up_inktober, 
  update_inktober_state_to_gsheets
)
from utils.config_utils import is_done_this_day, is_done_this_week
from utils.constants import (
  APPROVE_SIGN,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_MODE_WEEKLY_PROMPTS,
  BOT_DISCORD_ID_WEIRD,
  DELAY, 
  DIR_OUTPUT,
  DISCORD_GUILD,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_NAME,
  GSHEET_WEEKLYPROMPT_COLUMN_APPROVED,
  GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL,
  GSHEET_WEEKLYPROMPT_COLUMN_REJECTED,
  GSHEET_WEEKLYPROMPT_COLUMN_STATE,
  WEEKLYPROMPTS_APPROVE_CHANNEL,
  WEEKLYPROMPTS_RECEIVE_CHANNEL,
  WEEKLYPROMPTS_REPORT_CHANNEL, 
  NOT_APPROVE_SIGN, 
  PATH_IMG_HAPPY, 
  PATH_IMG_PALETTOBER_POSTER,
  PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK,
  PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK_STATUS,
  PAYLOAD_PARAM_MESSAGE_TO_SUBMITTED_ARTWORK,
  WEEKLYPROMPT_DICT_WEEK_TO_PROMPT,
  WEEKLYPROMPTS_APPROVE_CHANNEL,
  WEEKLYPROMPTS_RECEIVE_CHANNEL,
  WEEKLYPROMPTS_UPLOAD_LIMIT
)
from utils.messages import MESSAGE_APPROVE_ARTWORK, MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE, MESSAGE_WEEKLYPROMPT_WEEK_MESSAGE, MESSAGE_WEEKLYPROMPT_WRONG_REQUEST_INPUT, MESSAGE_WEEKLYPROMPT_WRONG_WEEK
from utils.utils import (
  calculate_score, 
  clear_folder, 
  get_day_from_message,
  get_processed_input_message, 
  get_rank_emoji, 
  get_today_date,
  get_today_week,
  get_week_from_datetime,
  remove_messages
)


async def task():
  channel_to_send = os.getenv(WEEKLYPROMPTS_REPORT_CHANNEL)
  # await DiscordBot().get_channel(GUILD, channel_to_send).send(
  # "**Hope you all have enjoyed Palettober! I will stop the reminder messages from here on. \nWe will have more things coming our way so stay tuned uwu**",
  # file = discord.File(PATH_IMG_HAPPY)
  # )

  print("[INFO] Starting WeeklyPrompt Applet...")
  while True:
    # do something
    delay: int = int(os.getenv(DELAY))
    await asyncio.sleep(delay)
    # try:
    await get_scores()
    # except Exception as e:
    #     await channel.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )
    

async def get_scores(is_command = False):
  # Pull changes from Gsheets
  #DiscordBot().set_up_after_run()
  # Ensures that the score report is only posted once a day, or when the bot restarts.
  if (not is_command) and is_done_this_day():
    return


  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  #print("report getscores", os.getenv(WEEKLYPROMPTS_REPORT_CHANNEL))
  channel_to_send = DiscordBot().get_channel(
    guild, 
    "bot-spam" if is_command else os.getenv(WEEKLYPROMPTS_REPORT_CHANNEL)
  )

  today_week = get_today_week()
  prompts = WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[today_week]

  if not is_done_this_week(
  #    hour=8
  ):
    message = \
      pystache.render(
        MESSAGE_WEEKLYPROMPT_WEEK_MESSAGE,
        {
          "bot_name": DiscordBot().bot.user.display_name,
          "week": today_week,
          "prompts": [
            {
              "id": id + 1,
              "emoji": prompt.emoji,
              "prompt": prompt.prompt
            }
            for id, prompt in enumerate(
              prompts
            )
          ],
        }
      )
    await channel_to_send.send(message)
  
  message = \
    pystache.render(
      MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE,
      {
        "game": "Weekly Prompts",
        "role": "@everyo",
        "prompts": [
          {
            "id": id + 1,
            "emoji": prompt.emoji,
            "prompt": prompt.prompt
          }
          for id, prompt in enumerate(
            prompts
          )
        ],
        "scores":  sorted([
          {
            "id": id + 1,
            "score": player.get_weeklyprompt_scores_sum(),
            "name": player.attributes[GSHEET_COLUMN_DISCORD],
            "emoji": get_rank_emoji(id + 1)
          }
          for id, player in enumerate(
            # Filter players with 0 score
            list(filter(
              lambda player: player.get_weeklyprompt_scores_sum() > 0,
              list(DiscordBot().players.values())
            ))
          )
        ],
        # Sort score in descending order
        key=lambda x: x["score"],
        reverse=True
        ),
      }
    )

  #print(message)

  await channel_to_send.send(message)

"""
When you mention the bot with the inktober entry,
you append your message to the queue.
This handler handles the message.
"""
async def on_message(message):
  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  #print(DiscordBot().bot.user.mentioned_in(message))
  #print(message.content)
  
  if (
    # If mentioned in artwork receiving channel
    message.channel.name == os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL) \
    
    # The message mentions the bot
    and (
      DiscordBot().bot.user.mentioned_in(message) \
      # or re.search(f"@{DiscordBot().bot.user.name}", message.content) \
      or re.search(BOT_DISCORD_ID_WEIRD, message.content) \
    ) \
    # The author is not the bot
    and message.author != DiscordBot().bot.user
  ):

    #print("TEXT: ", message.content)
    try:
      message_payload = get_processed_input_message(message.content)
    except Exception as err:
      print(err)
      message = \
        pystache.render(
          MESSAGE_WEEKLYPROMPT_WRONG_REQUEST_INPUT,
          {
            "author": message.author.id,
            "bot_name": DiscordBot().bot.user.display_name
          }
        )
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(message)

    #print(message_payload)
    week_to_approve = int(message_payload["week"])

    """
    Validate week
    """
    if (week_to_approve > int(get_recorded_week())):
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        f"<@{message.author.id}> ** You cannot submit into the future! **"
      )
    elif (week_to_approve < 3):
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        f"<@{message.author.id}> ** You cannot choose a week before week 3... **"
      )
    elif week_to_approve < get_today_week():
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        f"<@{message.author.id}> ** You cannot choose a week before the current week... **"
      )

    prompt_ids = [int(i) for i in message_payload["prompt"]]
    
    """
    Validate prompts
    """
    for prompt_id in prompt_ids:
     if (
       prompt_id < 1 
       or prompt_id > len(WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[week_to_approve]) \
     ):
      message = \
        pystache.render(
          MESSAGE_WEEKLYPROMPT_WRONG_WEEK,
          {
            "week": get_recorded_week(),
            "author": message.author.id,
            "prompts": [
              {
                "id": id + 1,
                "emoji": prompt.emoji,
                "prompt": prompt.prompt
              }
              for id, prompt in enumerate(
                WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[week_to_approve]
              )
            ],
          }
        )
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        message 
      )

    prompts = [WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[week_to_approve][prompt_id] for prompt_id in prompt_ids]
      
    # if no io/ existing in the system, make io/
    if "io" not in os.listdir(os.getcwd()):
      os.mkdir(DIR_OUTPUT)

    # if len(message.attachments) <= 0 :
      # return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        # f"<@{message.author.id}> You did not attach an artwork image!"
      # )

    # Check if the player has uploaded his limit.
    week = get_today_week()
    player = DiscordBot().players[str(message.author.id)]

    if player.get_weeklyprompt_scores_at_week(week) >= WEEKLYPROMPTS_UPLOAD_LIMIT:
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        "You have already been credited the maximum score for the week!"
      )

    response = requests.get(message.attachments[0].url)

    # Save file to io folder
    filename = "io/%s.%s" % (
      "tmp",
      str(message.attachments[0].url).split(".")[-1]
    )

    with open(filename, "wb") as f:
      f.write(response.content)

    approve_message = pystache.render(
      MESSAGE_APPROVE_ARTWORK,
      {
        "prompts": prompts,
        "jumpUrl": message.jump_url
      }
    )

    # Send approval message
    message_approve_artwork = await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL)).send(
      #"Theme: %s **%s**. \nApprove this post? %s" % (prompts.emoji, prompts.prompt, message.jump_url),
      approve_message,
      file = discord.File(os.path.join(os.getcwd(), filename))
    )

    message_approval_status = await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
      "Received Weekly Prompt Submission! <@%s>" % (message.author.id)
    )

    payload_to_store = {
        "week" : week_to_approve, 
        "prompts": [
          {
            "id": id + 1,
            "emoji": prompt.emoji,
            "prompt": prompt.prompt
          }
          for id, prompt in enumerate(
            prompts
          )
        ],
        PAYLOAD_PARAM_MESSAGE_TO_SUBMITTED_ARTWORK : message.id, 
        PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK : message_approve_artwork.id,
        PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK_STATUS : message_approval_status.id
    }

    #print(payload_to_store)

    # To store in db for persistence.
    player.add_message_id_to_set_by_type(
      message_approve_artwork.id, 
      GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL,
      payload_to_store
    )

    # To store in queue for retrieval.
    DiscordBot().approve_queue[ART_FIGHT_MODE_WEEKLY_PROMPTS][message_approve_artwork.id] = payload_to_store


    await message_approve_artwork.add_reaction(APPROVE_SIGN)
    await message_approve_artwork.add_reaction(NOT_APPROVE_SIGN)

    clear_folder()

    await DiscordBot().update_players_to_db()

  else:
    # The message might be a command. run it.
    await DiscordBot().bot.process_commands(message)

# In the event the admins add a reaction to approve/disapprove
async def on_raw_reaction_add(payload):
  approve_request_to_service = None
  message_approve_artwork_id = payload.message_id
  approver = payload.member
  emoji = payload.emoji.name
  channel_id = payload.channel_id
  print(emoji)

  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  message_approve_artwork = await DiscordBot().bot.get_channel(channel_id).fetch_message(message_approve_artwork_id)

  # If not on approve channel
  if message_approve_artwork.channel.name != os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL):
    print("[ERR] Not in approve channel!")
    return

  # Ensure approver is of correct access rights
  if len(list(filter(lambda role: role.name in ["Senpai"], approver.roles))) == 0:
    print("[ERR] Not authorised to approve!")
    return 

  try:
    approve_request_to_service = \
        DiscordBot().approve_queue[ART_FIGHT_MODE_WEEKLY_PROMPTS][message_approve_artwork_id]
  except:
    print("Request Not found")
    return
  
  print("Approve Request: ", approve_request_to_service)
  week = approve_request_to_service["week"]

  message_artwork = await DiscordBot().get_message_by_id(
    os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL), 
    approve_request_to_service[PAYLOAD_PARAM_MESSAGE_TO_SUBMITTED_ARTWORK]
  )

  message_approval_status = await DiscordBot().get_message_by_id(
    os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL), 
    approve_request_to_service[PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK_STATUS]
  )

  player_id = message_artwork.author.id
  player = DiscordBot().players[str(player_id)]

  if emoji == APPROVE_SIGN:
    await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL)).send(
      "> <@%s> approved this post: %s" % (approver.id, message_artwork.jump_url)
    )

    player.increment_weeklyprompt_score_at_week(week, 1)

    player.move_message_id_across_types(
      message_approve_artwork_id, 
      GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL, 
      GSHEET_WEEKLYPROMPT_COLUMN_APPROVED
    )

    # Add tick to source artwork
    await message_artwork.add_reaction(APPROVE_SIGN)
    # Update status message
    await message_approval_status.edit(content="> <@%s> approved your artwork post: %s" % (approver.id, message_artwork.jump_url))
    await remove_messages([message_approve_artwork])

  elif emoji == NOT_APPROVE_SIGN:
    await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL)).send(
      "> <@%s> rejected this post: %s" % (approver.id, message_artwork.jump_url)
    )
    await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
      "> <@%s> Due to some reasons, your post is not accepted! Sorry... %s" % (message_artwork.author.id, message_artwork.jump_url),
    )

    player.move_message_id_across_types(
      message_approve_artwork_id, 
      GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL, 
      GSHEET_WEEKLYPROMPT_COLUMN_REJECTED
    )
    await message_artwork.add_reaction(NOT_APPROVE_SIGN)
    await remove_messages([message_approve_artwork])

  
  await DiscordBot().update_players_to_db()

