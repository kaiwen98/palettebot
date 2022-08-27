import os
import re

from utils.commons import DIR_OUTPUT

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
from config_loader import (
  ART_FIGHT_MODE_INKTOBER,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_STATE,
  GUILD, 
  DELAY,
  BIRTHDAY_REPORT_CHANNEL,
  INKTOBER_APPROVE_CHANNEL, 
  INKTOBER_RECEIVE_CHANNEL, 
  INKTOBER_REPORT_CHANNEL, 
  WAIFUWARS_APPROVE_CHANNEL,
  WAIFUWARS_RECEIVE_CHANNEL, 
  WAIFUWARS_REPORT_CHANNEL, 
  IS_HEROKU, 
  TOKEN, 
  call_stack,
)

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

from utils.commons import (
  DIR_OUTPUT, 
  DISCORD_CHANNEL_ART_GALLERY, 
  DISCORD_MESSAGES_LIMIT,
  EXTRAVAGANZA_ROLE,
  MEMBER_ROLE
)
from utils.utils import (
  get_num_days_away, 
  get_rank_emoji, 
  get_timestamp_from_curr_datetime, 
  get_today_date, 
  remove_messages
)

from utils.utils import (
  calculate_score, 
  clear_folder, 
  get_channel, 
  get_day_from_message, 
  get_rank_emoji, 
  get_today_date, 
  remove_messages
)

def process_string_name(inp_str):
  output = inp_str
  if re.search(r'_[0-9]\.[0-9a-zA-Z]+', inp_str):
    output = os.path.splitext(output)[0][:output.rfind("_")]
  elif re.search(r'.[0-9a-zA-Z]+', inp_str):
    output = os.path.splitext(output)[0]
  else:
    output = inp_str
  return output.replace("[Instagram] ", "[Instagram] @").replace("[Twitter] ", "[Twitter] @")

def get_list_of_artists(path):
  result_text = ""
  output = {}

  image_filenames = os.listdir(path)
  print(image_filenames)
  output[dir] = [process_string_name(i) for i in image_filenames]
  print(output)
  for i in output[dir]:
    result_text = result_text + i + "\n"
    with open(os.path.join(path, "artists.txt"), "w") as f:
      f.write(result_text)
    return result_text

async def get_all_members_text(input_channel, ctx):
  channel = None
  guild = DiscordBot().get_guild(GUILD)
  channel = DiscordBot().get_channel(guild, input_channel)

  if channel is None: 
    await ctx.send(
      "Channel not recognised. Make sure you spelt it right!"
    )
    return

  members = channel.members #finds members connected to the channel

  mem_names = [] #(list)
  for member in members:
    mem_names.append(member.name + "\n")

    await ctx.send(
      "".join(mem_names)
    )


async def get_photos(input_channel_name, palette_particulars, dd_begin, mm_begin, dd_end, mm_end, year, ctx): 
  """
  The code should look back to a large number of messages within a particular date range,
        Then downloads all images from artists who have the right permissions.

        TODO: Relocate this code to controller/artwork_extract.py 
  """

  global export_file
  is_no_images = True
  channel = None
  guild = DiscordBot().get_guild(GUILD)
  channel = DiscordBot().get_channel(guild, input_channel_name)
  artist_name_to_num_artworks = {}

  from_date = datetime(year, mm_begin, dd_begin, 0, 0, 0) - (timedelta(hours = 8) if os.getenv("ENV") == "production" else timedelta(hours = 0))
  to_date = datetime(year, mm_end, dd_end, 0, 0, 0) - (timedelta(hours = 8) if os.getenv("ENV") == "production" else timedelta(hours = 0))

  if channel is None: 
    await ctx.send(
      "Channel not recognised. Make sure you spelt it right!"
    )
    return

  messages = await channel.history(
    limit = DISCORD_MESSAGES_LIMIT,
  ).flatten()

  folder_name = get_timestamp_from_curr_datetime()

  if "io" not in os.listdir(os.getcwd()):
    os.mkdir(DIR_OUTPUT)

  os.mkdir(os.path.join(DIR_OUTPUT, folder_name))

  for message in messages:

    print(message.created_at)
    # Hash user name in dict
    if str(message.author) not in artist_name_to_num_artworks.keys():
      artist_name_to_num_artworks[str(message.author)] = 0

    # Before Startline, factoring timezone
    if (message.created_at < from_date): 
      print("Done!")
      break

    # After Deadline, factoring timezone
    if (message.created_at > to_date): 
      continue

    # skip messages with no attachments
    if len(message.attachments) <= 0:
      continue
  
    # If no permission to share, skip
    if get_fuzzily_discord_handle(str(message.author), palette_particulars) is None or \
        not verify_is_okay_to_share_by_discord_name(str(message.author), palette_particulars):
      print(message.author, " do not wish to share")
      continue

    print(message.author)
    print(message.content)
    print(message.attachments)
    print(artist_name_to_num_artworks) 

    response = requests.get(message.attachments[0].url)

    if artist_name_to_num_artworks[str(message.author)] >= 1:

      print("file exists")

      filename = "io/%s/%s.%s" % (
        folder_name, 
        pretty_print_social_handle_wrapper(
          name = str(message.author), 
          df = palette_particulars) \
        + "_%s" % (
          artist_name_to_num_artworks[str(message.author)]
        ),
        str(message.attachments[0].url).split(".")[-1]
      )

    else:

      filename = "io/%s/%s.%s" % (
        folder_name, 
        pretty_print_social_handle_wrapper(
          name = str(message.author), 
          df = palette_particulars
        ),
        str(message.attachments[0].url).split(".")[-1]
      )

    with open(filename, "wb") as f:
      artist_name_to_num_artworks[str(message.author)] += 1 
      f.write(response.content)

      is_no_images = False
      
    if is_no_images:
      return await ctx.send(
        "No artworks can be found!"
      )

    zip_name = "io/%s.zip" % (folder_name)
    zipFile = ZipFile(zip_name, 'w')

    curr_dir = os.path.join(os.getcwd(), "io", folder_name)
    await ctx.send(
      get_list_of_artists(curr_dir)
    )
    print(curr_dir)
    for file in os.listdir(curr_dir):
      print(os.path.join(curr_dir, file))
      zipFile.write(os.path.join(curr_dir, file), file)
    zipFile.close()

    link = ""

    try:
      link = upload_to_gdrive([zip_name])
    except:
      await ctx.send(
        "Certificate revoked. You need to regenerate the credentials by following this link and pushing to remote: https://pythonhosted.org/PyDrive/oauth.html"
            )

    await ctx.send(
      "Log in to Palette Exco Email to access the ZIP file! Link: %s" % link
          )

    clear_folder()

