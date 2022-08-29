from numpy import empty
from controller.excelHandler import get_player_from_gsheets, update_columns_to_gsheets
from models.Player import Player
from models.Singleton import Singleton
import discord
import discord.ext as d_ext
import pandas as pd
import time
import os

from utils.commons import (
  DISCORD_GUILD, 
  DISCORD_TOKEN,
  DOCID_MASTER_TRACKER,
  GSHEET_COLUMN_NAME,
  GSHEET_PLAYER_COLUMNS
)

class DiscordBot(metaclass=Singleton):
  def __init__(self):
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    self.token = os.getenv(DISCORD_TOKEN)
    self.bot = discord.ext.commands.Bot(command_prefix='> ', intents=intents)
    self.approve_queue = []
    self.guild_name = os.getenv(DISCORD_GUILD)
    self.invite_links = {}
    self.extravaganza_invite_link = None
    self.players = {}
    self.update_delay = 60 * 5

  def run(self):
    self.bot.run(self.token)

  def initialize_players(self, df):
    for index, row in df.iterrows():
      key = row[GSHEET_COLUMN_NAME]
      self.players[key] = Player(row)

  def update_players_to_db(self):
    dataframes = map(
      lambda player: player.export_to_df_row(),
      self.players    
    )

    output_df = pd.concat(dataframes)

    update_columns_to_gsheets(
      input_df=output_df,
      doc_id=os.getenv(DOCID_MASTER_TRACKER),
      name_dict=None,
      column_names=GSHEET_PLAYER_COLUMNS
    )

  def task(self):
    df = get_player_from_gsheets()
    self.initialize_players(df)
    print("Launching Gsheet update task...")
    while True:
      self.update_players_to_db()
      time.sleep(self.update_delay)
      print("Gsheet updated")

  def get_guild(self, guild_name):
    if guild_name is None:
      guild_name = self.get_guild(os.getenv(DISCORD_GUILD))
    filtered_guilds = \
      list(filter(
        lambda guild: guild.name == guild_name,
        self.bot.guilds
      ))

    return None if len(filtered_guilds) == 0 else filtered_guilds[0]

  def get_channel(self, guild, channel_name):
    print(channel_name)
    if guild is None:
      guild = self.get_guild(os.getenv(DISCORD_GUILD))

    filtered_channels = list(filter(
      lambda channel: channel_name in channel.name,
      guild.channels
    ))

    return None if len(filtered_channels) == 0 else guild.get_channel(filtered_channels[0].id)

