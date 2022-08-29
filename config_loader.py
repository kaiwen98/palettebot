import os
from dotenv import (
  load_dotenv,
  set_key,
)
from datetime import datetime
import discord
from discord.ext import commands
import getopt, sys
from models.DiscordBot import DiscordBot
from utils.commons import (
  ART_FIGHT_MODE_INKTOBER, 
  ART_FIGHT_MODE_NOTHING,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_MODE_WEEKLY_PROMPTS
)

"""
Global variables
"""

global_config_params = {
  "GLOBAL_DATE": None,
  "GLOBAL_DELAY": None
}

def set_config_param(key, value):
  global global_config_params
  global_config_params[key] = value

def get_config_param(key):
  global global_config_params
  return global_config_params[key]

def set_recorded_date(date):
  global global_config_params
  global_config_params["GLOBAL_DATE"] = date

def get_delay():
  global global_config_params
  return global_config_params["GLOBAL_DELAY"]

def set_delay(delay):
  global global_config_params
  global_config_params["GLOBAL_DELAY"] = delay

def get_recorded_date():
  global global_config_params
  return global_config_params["GLOBAL_DATE"]

def load_config(env):
  print("Loading config")
  dotenv_path = os.path.join(os.path.dirname(__file__), f".env.{env}")
  load_dotenv(dotenv_path)
  set_key(dotenv_path, "ENV", env)
  is_production_env = os.getenv("ENV") == 'production'

  art_fight_state = ART_FIGHT_MODE_NOTHING

  if is_production_env:
    art_fight_state = ART_FIGHT_MODE_INKTOBER if datetime.now().month == 10 else ART_FIGHT_MODE_NOTHING
  else:
    art_fight_state = ART_FIGHT_MODE_INKTOBER

    set_key(dotenv_path, "ART_FIGHT_STATE", str(art_fight_state))
    DiscordBot()

def load_env_by_command_line_args():
  # Remove 1st argument from the
  # list of command line arguments
  argumentList = sys.argv[1:]

  # Options
  options = "e:"

  # Long options
  long_options = ["env="]

  try:
    # Parsing argument
    arguments, values = getopt.getopt(argumentList, options, long_options)

    # checking each argument
    for currentArgument, currentValue in arguments:
      if currentArgument in ("-e", "--env"):
        load_config(currentValue)

  except getopt.error as err:
    # output error, and return with an error code
    print (str(err))

