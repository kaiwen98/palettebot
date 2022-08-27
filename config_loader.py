import os
from dotenv import (
  load_dotenv,
  set_key,
)
from datetime import datetime
import discord
from discord.ext import commands
import getopt, sys
from controller.DiscordBot import DiscordBot

IS_PRODUCTION = os.getenv("ENV") == 'production'
TOKEN = None
GUILD = None

INKTOBER_RECEIVE_CHANNEL = "INKTOBER_RECEIVE_CHANNEL"
INKTOBER_REPORT_CHANNEL = "INKTOBER_REPORT_CHANNEL"
INKTOBER_APPROVE_CHANNEL = "INKTOBER_APPROVE_CHANNEL"
WAIFUWARS_APPROVE_CHANNEL = "WAIFUWARS_APPROVE_CHANNEL"
WAIFUWARS_RECEIVE_CHANNEL = "WAIFUWARS_RECEIVE_CHANNEL"
WAIFUWARS_REPORT_CHANNEL = "WAIFUWARS_REPORT_CHANNEL"
DELAY = "DELAY"
ART_FIGHT_MODE_INKTOBER = 1
ART_FIGHT_MODE_WAIFUWARS = 0
ART_FIGHT_MODE_WEEKLY_PROMPTS = 0
ART_FIGHT_MODE_NOTHING = -1

BIRTHDAY_REPORT_CHANNEL = None

global_date = None

if IS_PRODUCTION:
    ART_FIGHT_STATE = ART_FIGHT_MODE_INKTOBER if datetime.now().month == 10 else ART_FIGHT_MODE_NOTHING
else:
    ART_FIGHT_STATE = ART_FIGHT_MODE_INKTOBER

def set_recorded_date(date):
    global global_date
    global_date = date

def get_recorded_date():
    return global_date

def load_config(env):
    print("Loading config")
    global TOKEN, GUILD, INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL
    global BIRTHDAY_REPORT_CHANNEL, INKTOBER_REPORT_CHANNEL, IS_PRODUCTION, DELAY, WAIFUWARS_APPROVE_CHANNEL, WAIFUWARS_RECEIVE_CHANNEL, WAIFUWARS_REPORT_CHANNEL
    dotenv_path = os.path.join(os.path.dirname(__file__), f".env.{env}")
    print(dotenv_path)
    load_dotenv(dotenv_path)

    # If IS_HEROKU is set, the app is deployed.
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')

    set_key(dotenv_path, "ENV", env)

    # INKTOBER_RECEIVE_CHANNEL = os.getenv('INKTOBER_RECEIVE_CHANNEL')
    # INKTOBER_REPORT_CHANNEL = os.getenv('INKTOBER_REPORT_CHANNEL')
    # print("report", INKTOBER_REPORT_CHANNEL)
    # INKTOBER_APPROVE_CHANNEL = os.getenv('INKTOBER_APPROVE_CHANNEL')

    # WAIFUWARS_RECEIVE_CHANNEL = os.getenv('WAIFUWARS_RECEIVE_CHANNEL')
    # WAIFUWARS_REPORT_CHANNEL = os.getenv('WAIFUWARS_REPORT_CHANNEL')
    # WAIFUWARS_APPROVE_CHANNEL = os.getenv('WAIFUWARS_APPROVE_CHANNEL')

    # BIRTHDAY_REPORT_CHANNEL = os.getenv('BIRTHDAY_REPORT_CHANNEL')

    # DELAY = os.getenv('DELAY')

    #print(os.environ)

    # Initialise DiscordBot.
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

