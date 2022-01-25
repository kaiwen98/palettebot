import os
from dotenv import load_dotenv
from datetime import datetime
import discord
from discord.ext import commands

IS_HEROKU = None
TOKEN = None
GUILD = None

INKTOBER_RECEIVE_CHANNEL = None
INKTOBER_REPORT_CHANNEL = None
INKTOBER_APPROVE_CHANNEL = None
WAIFUWARS_APPROVE_CHANNEL = None
WAIFUWARS_RECEIVE_CHANNEL = None
WAIFUWARS_REPORT_CHANNEL = None
bot = None
DELAY = None
ART_FIGHT_MODE_INKTOBER = 1
ART_FIGHT_MODE_WAIFUWARS = 0
ART_FIGHT_MODE_NOTHING = -1
if IS_HEROKU:
    ART_FIGHT_STATE = ART_FIGHT_MODE_INKTOBER if datetime.now().month == 10 else ART_FIGHT_MODE_NOTHING
else:
    ART_FIGHT_STATE = ART_FIGHT_MODE_NOTHING
call_stack = []
call_stack_waifuwars = []
curr_day = 3

def load_config():
    print("hi")
    global TOKEN, GUILD, INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL
    global BIRTHDAY_REPORT_CHANNEL, INKTOBER_REPORT_CHANNEL, IS_HEROKU, DELAY, WAIFUWARS_APPROVE_CHANNEL, WAIFUWARS_RECEIVE_CHANNEL, WAIFUWARS_REPORT_CHANNEL
    global bot
    load_dotenv()
    IS_HEROKU = "IS_HEROKU" in os.environ.keys()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')

    INKTOBER_RECEIVE_CHANNEL = "art-gallery🥰" if IS_HEROKU else "exco-chat"
    INKTOBER_REPORT_CHANNEL = "general" if IS_HEROKU else "bot-spam"
    INKTOBER_APPROVE_CHANNEL = "bot-spam"

    WAIFUWARS_RECEIVE_CHANNEL = "art-gallery🥰" if IS_HEROKU else "exco-chat"
    WAIFUWARS_REPORT_CHANNEL = "general" if IS_HEROKU else "exco-chat"
    WAIFUWARS_APPROVE_CHANNEL = "art-gallery🥰" if IS_HEROKU else "exco-chat"

    BIRTHDAY_REPORT_CHANNEL = "general" if IS_HEROKU else "bot-spam"

    DELAY = 300 if IS_HEROKU else 10
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    bot = commands.Bot(command_prefix='> ', intents=intents)
    print("done")

load_config()