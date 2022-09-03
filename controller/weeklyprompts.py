from datetime import datetime
import pystache
import os
from config_loader import (
  get_recorded_date, 
  set_recorded_date
)
from models.DiscordBot import DiscordBot
import discord
import pandas as pd
import requests
import asyncio

from controller.excelHandler import (
  get_fuzzily_discord_handle, 
  set_up_inktober, 
  update_inktober_state_to_gsheets
)
from utils.constants import (
  APPROVE_SIGN,
  ART_FIGHT_MODE_WEEKLY_PROMPTS,
  DELAY, 
  DIR_OUTPUT,
  DISCORD_GUILD,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_NAME,
  GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL,
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
from utils.messages import MESSAGE_APPROVE_ARTWORK, MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE
from utils.utils import (
  calculate_score, 
  clear_folder, 
  get_day_from_message, 
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

  print("Starting WeeklyPrompt Applet...")
  while True:
    # do something

    # try:
    await get_scores()
    # except Exception as e:
    #     await channel.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )
    delay: int = int(os.getenv(DELAY))
    await asyncio.sleep(delay)

async def get_scores(command = False):

  # Ensures that the score report is only posted once a day, or when the bot restarts.
  if not command and (get_recorded_date() == get_today_date()):
    return

  set_recorded_date(get_today_date())

  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  print("report getscores", os.getenv(WEEKLYPROMPTS_REPORT_CHANNEL))
  channel_to_send = DiscordBot().get_channel(
    guild, 
    "bot-spam" if command else os.getenv(WEEKLYPROMPTS_REPORT_CHANNEL)
  )

  today_week = get_today_week()
  prompts = WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[today_week]
  
  message = \
    pystache.render(
      MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE,
      {
        "game": "Weekly Prompts",
        "role": "@everyone",
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
            "emoji": get_rank_emoji(id)
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

  await channel_to_send.send(message)

async def update_inktober(user, state, date):
  df_inktober = set_up_inktober()

  df_discord_members = pd.DataFrame({
    "Discord": [user.name + "#" + str(user.discriminator)],
    "uid" : [user.id],
  })

  print(df_discord_members)

  for index, row in df_inktober.iterrows():
    # iterates over the sheet
    # print(row[GSHEET_COLUMN_DISCORD])
    if get_fuzzily_discord_handle(row[GSHEET_COLUMN_DISCORD], df_discord_members, get_uid=True) is None:
      continue


    state_ls = list(row[GSHEET_WEEKLYPROMPT_COLUMN_STATE])
    state_ls[date] = str(state)
    df_inktober.at[index, GSHEET_WEEKLYPROMPT_COLUMN_STATE] = "".join(state_ls)
    # print("HEREEEEEEEEEEEE", _df_inktober.at[index, GSHEET_WEEKLYPROMPT_COLUMN_STATE])
    update_inktober_state_to_gsheets(df_inktober)

"""
When you mention the bot with the inktober entry,
you append your message to the queue.
This handler handles the message.
"""
async def on_message(message):
  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  print(DiscordBot().bot.user.mentioned_in(message))
  if (
    # If mentioned in artwork receiving channel
    message.channel.name == os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL) and \
    # The message mentions the bot
    DiscordBot().bot.user.mentioned_in(message) and \
    # The author is not the bot
    message.author != DiscordBot().bot.user
  ):

    print("TEXT: ", message.content)

    week_to_approve = get_day_from_message(message)
    prompt_ids = map(lambda x: int(x.strip()), message.content.split(" "))
    prompts = [WEEKLYPROMPT_DICT_WEEK_TO_PROMPT[week_to_approve][prompt_id] for prompt_id in prompt_ids]

    # if no io/ existing in the system, make io/
    if "io" not in os.listdir(os.getcwd()):
      os.mkdir(DIR_OUTPUT)

    if len(message.attachments) <= 0 :
      return await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL)).send(
        "You did not attach an artwork image!"
      )

    # Check if the player has uploaded his limit.
    week = get_today_week()
    player = DiscordBot().players[message.author.id]

    if player.get_weeklyprompt_scores_at_week(week) > WEEKLYPROMPTS_UPLOAD_LIMIT:
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
        "prompts": [{
          "emoji": prompt.emoji,
          "prompt": prompt.prompt
        } for prompt in prompts],
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
        "prompts": prompts,
        PAYLOAD_PARAM_MESSAGE_TO_SUBMITTED_ARTWORK : message.id, 
        PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK : message_approve_artwork.id,
        PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK_STATUS : message_approval_status.id
    }

    DiscordBot().players[message.author.name].add_message_id_to_set_by_type(
      message_approve_artwork.id, 
      GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL,
      payload_to_store
    )

    await message_approve_artwork.add_reaction(APPROVE_SIGN)
    await message_approve_artwork.add_reaction(NOT_APPROVE_SIGN)

    clear_folder()

  else:
    # The message might be a command. run it.
    await DiscordBot().bot.process_commands(message)

# In the event the admins add a reaction to approve/disapprove
async def on_raw_reaction_add(payload):
  approve_request_to_service = None
  message_approve_artwork_id = payload.message_id
  approver = payload.member
  emoji = payload.emoji.name
  print(emoji)

  guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
  message_approve_artwork = await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL)).fetch_message(message_approve_artwork_id)

  # If not on approve channel
  if message_approve_artwork.channel.name != os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL):
    return

  # Ensure approver is of correct access rights
  if len(list(filter(lambda role: role.name in ["Senpai"], approver.roles))) == 0:
    return 

  try:
    approve_request_to_service = \
        DiscordBot().get_player_by_id(message_approve_artwork.author.id) \
        .message_id_sets[GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL] \
        .get(message_approve_artwork_id)
  except:
    return

  week = approve_request_to_service["week"]

  message_artwork = await DiscordBot().get_message_by_id(
    os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL), 
    approve_request_to_service[PAYLOAD_PARAM_MESSAGE_TO_SUBMITTED_ARTWORK]
  )

  message_approval_status = await DiscordBot().get_message_by_id(
    os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL), 
    approve_request_to_service[PAYLOAD_PARAM_MESSAGE_TO_APPROVE_ARTWORK_STATUS]
  )

  artist_name = message_artwork.author.name

  if emoji == APPROVE_SIGN:
    await DiscordBot().get_channel(guild, os.getenv(WEEKLYPROMPTS_APPROVE_CHANNEL)).send(
      "> <@%s> approved this post: %s" % (approver.id, message_artwork.jump_url)
    )

    DiscordBot().players[artist_name].increment_weeklyprompt_score_at_week(week, 1)

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
    await message_artwork.add_reaction(NOT_APPROVE_SIGN)
    await remove_messages([message_approve_artwork])
