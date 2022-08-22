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

IS_HEROKU = None
TOKEN = None
GUILD = None

INKTOBER_RECEIVE_CHANNEL = None
INKTOBER_REPORT_CHANNEL = None
INKTOBER_APPROVE_CHANNEL = None
WAIFUWARS_APPROVE_CHANNEL = None
WAIFUWARS_RECEIVE_CHANNEL = None
WAIFUWARS_REPORT_CHANNEL = None
DELAY = None
ART_FIGHT_MODE_INKTOBER = 1
ART_FIGHT_MODE_WAIFUWARS = 0
ART_FIGHT_MODE_WEEKLY_PROMPTS = 0
ART_FIGHT_MODE_NOTHING = -1
if IS_HEROKU:
    ART_FIGHT_STATE = ART_FIGHT_MODE_INKTOBER if datetime.now().month == 10 else ART_FIGHT_MODE_NOTHING
else:
    ART_FIGHT_STATE = ART_FIGHT_MODE_NOTHING
call_stack = []
call_stack_waifuwars = []
curr_day = 3

def load_config(env):
    global TOKEN, GUILD, INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL
    global BIRTHDAY_REPORT_CHANNEL, INKTOBER_REPORT_CHANNEL, IS_HEROKU, DELAY, WAIFUWARS_APPROVE_CHANNEL, WAIFUWARS_RECEIVE_CHANNEL, WAIFUWARS_REPORT_CHANNEL
    dotenv_path = os.path.join(os.path.dirname(__file__), f".env.{env}")
    print(dotenv_path)
    load_dotenv(dotenv_path)

    # If IS_HEROKU is set, the app is deployed.
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')

    set_key(dotenv_path, "ENV", env)

    INKTOBER_RECEIVE_CHANNEL = os.getenv('INKTOBER_RECEIVE_CHANNEL')
    INKTOBER_REPORT_CHANNEL = os.getenv('INKTOBER_REPORT_CHANNEL')
    INKTOBER_APPROVE_CHANNEL = os.getenv('INKTOBER_APPROVE_CHANNEL')

    WAIFUWARS_RECEIVE_CHANNEL = os.getenv('WAIFUWARS_RECEIVE_CHANNEL')
    WAIFUWARS_REPORT_CHANNEL = os.getenv('WAIFUWARS_REPORT_CHANNEL')
    WAIFUWARS_APPROVE_CHANNEL = os.getenv('WAIFUWARS_APPROVE_CHANNEL')

    BIRTHDAY_REPORT_CHANNEL = os.getenv('BIRTHDAY_REPORT_CHANNEL')

    DELAY = os.getenv('DELAY')

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

