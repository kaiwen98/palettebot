from datetime import datetime
import os
from controller.DiscordBot import DiscordBot
import discord
import pandas as pd
import requests
import asyncio
from config_loader import GUILD, INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL, INKTOBER_REPORT_CHANNEL, IS_HEROKU, DELAY
import config_loader as cfg
from controller.excelHandler import INKTOBER_STATE, MEMBER_INFO_COL_DISCORD, STATE_APPROVED, STATE_UNDER_APPROVAL, get_fuzzily_discord_handle, set_up_inktober, update_inktober_state_to_gsheets
from utils.commons import APPROVE_SIGN, DIR_OUTPUT, NOT_APPROVE_SIGN, PATH_IMG_HAPPY, PATH_IMG_PALETTOBER_POSTER
from utils.utils import calculate_score, clear_folder, get_channel, get_day_from_message, get_rank_emoji, get_today_date, remove_messages


DICT_DAY_TO_PROMPT = {
  1: "Cactus",
  2: "Pitcher Plant",
  3: "Climbing Plant",
  4: "Flowers",
  5: "Seedling",
  6: "Terrarium",
  7: "Forest",
  8: "Mushroom",
  9: "Venus Flytrap",
  10: "Rafflesia",
  11: "Dinner",
  12: "Void Deck",
  13: "Coffeeshop",
  14: "Playground",
  15: "Working from Home",
  16: "Ice-cream",
  17: "Bus/Train",
  18: "Rain",
  19: "Park",
  20: "Convenience Store",
  21: "Witch",
  22: "Skull",
  23: "Haunted",
  24: "Grave",
  25: "Vampire",
  26: "Candles",
  27: "Bats",
  28: "Bugs",
  29: "Classroom",
  30: "Dolls",
  31: "Your Worst Fear"
}

async def inktober_task():
  counter = 0
  channel_to_send = INKTOBER_REPORT_CHANNEL
  # await DiscordBot().get_channel(GUILD, channel_to_send).send(
  # "**Hope you all have enjoyed Palettober! I will stop the reminder messages from here on. \nWe will have more things coming our way so stay tuned uwu**",
  # file = discord.File(PATH_IMG_HAPPY)
  # )
  while True:
    # do something

    # try:
    await get_scores()
    # except Exception as e:
    #     await channel.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )
    await asyncio.sleep(int(DELAY))

async def get_scores(command = False):
  print("LOOK!", cfg.curr_day, get_today_date(), datetime.now())
  if not command and (cfg.curr_day == get_today_date()):
    return
  cfg.curr_day = get_today_date()
  output = []
  rank = []
  df_inktober = set_up_inktober()
  guild = DiscordBot().get_guild(GUILD)
  channel_to_send = DiscordBot().get_channel(
    guild, 
    "bot-spam" if command else INKTOBER_REPORT_CHANNEL
  )

  df_discord_members = pd.DataFrame({
    "Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
    "uid" : [i.id for i in guild.members],
  })

  print(df_discord_members)

  if get_today_date() < 11: 
    prompt_type = ":potted_plant:"
  elif get_today_date() < 21:
    prompt_type = ":house:"
  else:
    prompt_type = ":ghost:"
    output.append(
      "Good Morning! Today's Palette Drawtober prompt is ... %s **%s**!\n\n" % (prompt_type, DICT_DAY_TO_PROMPT[get_today_date()])
    )

    output.append("**Drawtober Scores!**\n")

    for index, row in df_inktober.iterrows():
      try:

        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members) is None:
          continue

        user_score_pair = (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members), calculate_score(row[INKTOBER_STATE]))

        if str(STATE_APPROVED) in list(row[INKTOBER_STATE]):
          rank.append(user_score_pair)

      except Exception as e:
        continue

    rank.sort(key = lambda tup: tup[1], reverse = True)

    for index, _user_score_pair in enumerate(rank):
      output.append("Rank %s %s .... **%s** [Score: %s]\n" % (
        index + 1,
        get_rank_emoji(index + 1),
        _user_score_pair[0], 
        _user_score_pair[1],
      )
                    )

    if len(rank) == 0:
      output.append("No submissions yet.. Draw something!")

    await channel_to_send.send(
      "**:art: :speaker: Your friendly DRAWTOBER announcement!**\n%s\n" % ("https://discord.com/channels/668080486257786880/747465326748368947/893389786667163659") + "".join(output),
      file = discord.File(PATH_IMG_PALETTOBER_POSTER)
    )

async def update_inktober(user, state, date):
  df_inktober = set_up_inktober()

  df_discord_members = pd.DataFrame({
    "Discord": [user.name + "#" + str(user.discriminator)],
    "uid" : [user.id],
  })

  print(df_discord_members)

  for index, row in df_inktober.iterrows():
    # iterates over the sheet
    # print(row[MEMBER_INFO_COL_DISCORD])
    if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members, get_uid=True) is None:
      continue


    state_ls = list(row[INKTOBER_STATE])
    state_ls[date] = str(state)
    df_inktober.at[index, INKTOBER_STATE] = "".join(state_ls)
    # print("HEREEEEEEEEEEEE", _df_inktober.at[index, INKTOBER_STATE])
    update_inktober_state_to_gsheets(df_inktober)

"""
When you mention the bot with the inktober entry,
you append your message to the queue.
This handler handles the message.
"""
async def on_message_inktober(message, approve_queue):
  guild = DiscordBot().get_guild(GUILD)
  print(DiscordBot().bot.user.mentioned_in(message))
  if (
    # If mentioned in artwork receiving channel
    message.channel.name == INKTOBER_RECEIVE_CHANNEL and \
    # The message mentions the bot
    DiscordBot().bot.user.mentioned_in(message) and \
    # The author is not the bot
    message.author != DiscordBot().bot.user
  ):

    print("TEXT: ", message.content)
    day_to_approve = get_day_from_message(message)

    # if no io/ existing in the system, make io/
    if "io" not in os.listdir(os.getcwd()):
      os.mkdir(DIR_OUTPUT)
      print("there")

    if len(message.attachments) <= 0 :
      return await DiscordBot().get_channel(guild, INKTOBER_RECEIVE_CHANNEL).send(
        "You did not attach an artwork image!"
      )

    response = requests.get(message.attachments[0].url)

    # Save file to io folder
    filename = "io/%s.%s" % (
      "tmp",
      str(message.attachments[0].url).split(".")[-1]
    )

    with open(filename, "wb") as f:
      f.write(response.content)

      # Send approval message
      message_approve_artwork = await DiscordBot().get_channel(guild, INKTOBER_APPROVE_CHANNEL).send(
        "Theme: %s. \nApprove this post? %s" % (DICT_DAY_TO_PROMPT[day_to_approve], message.jump_url),
        file = discord.File(os.path.join(os.getcwd(), filename))
      )

      await update_inktober(message.author, STATE_UNDER_APPROVAL, day_to_approve - 1)

      approve_queue.append({
        "type" : "inktober",
        "day" : day_to_approve, 
        "message_artwork" : message, 
        "message_approve_artwork" : message_approve_artwork
      })

      await message_approve_artwork.add_reaction(APPROVE_SIGN)
      await message_approve_artwork.add_reaction(NOT_APPROVE_SIGN)

      await DiscordBot().get_channel(guild, INKTOBER_RECEIVE_CHANNEL).send(
        "Received! <@%s>" % (message.author.id)
      )

      clear_folder()

  else:
    # The message might be a command. run it.
    await DiscordBot().bot.process_commands(message)

# In the event the admins add a reaction to approve/disapprove
async def on_raw_reaction_add_inktober(payload, approve_queue):
  message_approve_artwork_id = payload.message_id
  user = payload.member
  emoji = payload.emoji.name
  print(emoji)

  guild = DiscordBot().get_guild(GUILD)
  message_approve_artwork = await DiscordBot().get_channel(guild, INKTOBER_APPROVE_CHANNEL).fetch_message(message_approve_artwork_id)

  # print(message.id, type(message.id), list(approve_queue.keys()))

  # If approved artwork not in queue, return
  if message_approve_artwork.id not in [i["message_approve_artwork"].id for i in approve_queue]:
    return

  # specifies the channel restriction
  # TODO: switch to Senpai
  if user.name not in ["okai_iwen", "tako", "Hoipus"]:
    return 

  # If not on approve channel
  if message_approve_artwork.channel.name != INKTOBER_APPROVE_CHANNEL:
    return

  approve_request_to_service = tuple(filter(lambda i: i["message_approve_artwork"].id == message_approve_artwork.id, approve_queue))[0]

  day = approve_request_to_service["day"]
  message_artwork = approve_request_to_service["message_artwork"]

  approve_queue.remove(approve_request_to_service)

  print(approve_queue)

  if emoji == APPROVE_SIGN:
    await get_channel(DiscordBot().bot, GUILD, INKTOBER_APPROVE_CHANNEL).send(
      "> <@%s> approved this post: %s" % (user.id, message_artwork.jump_url),
    )
    await update_inktober(message_artwork.author, STATE_APPROVED, day - 1)

  elif emoji == NOT_APPROVE_SIGN:
    await get_channel(DiscordBot().bot, GUILD, INKTOBER_APPROVE_CHANNEL).send(
      "> <@%s> rejected this post: %s" % (user.id, message_artwork.jump_url),
    )
    await get_channel(DiscordBot().bot, GUILD, INKTOBER_RECEIVE_CHANNEL).send(
      "> <@%s> Due to some reasons, your post is not accepted! Sorry... %s" % (message_artwork.author.id, message_artwork.jump_url),
    )
    await remove_messages([message_approve_artwork])
