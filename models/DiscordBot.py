from numpy import empty
from controller.excelHandler import (
  get_fuzzily_discord_handle,
  get_player_from_gsheets, 
  update_columns_to_gsheets
)
from models.Player import Player
from models.Singleton import Singleton
import discord
import discord.ext as d_ext
import pandas as pd
import time
import os

import uuid

from utils.constants import (
  ART_FIGHT_MODE_INKTOBER,
  ART_FIGHT_MODE_WAIFUWARS,
  ART_FIGHT_MODE_WEEKLY_PROMPTS,
  ART_FIGHT_MODES,
  ART_FIGHT_STATE,
  DEFAULT_INKTOBER_STATE_DATA,
  DEFAULT_MESSAGES_DATA,
  DEFAULT_WEEKLYPROMPT_STATE_DATA,
  DISCORD_GUILD,
  DISCORD_MESSAGES_LIMIT, 
  DISCORD_TOKEN,
  DOCID_MASTER_TRACKER,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_DISCORD_ID,
  GSHEET_COLUMN_NAME,
  GSHEET_COLUMNS_MESSAGE_STATES,
  GSHEET_INKTOBER_COLUMN_STATE,
  GSHEET_PLAYER_COLUMNS,
  GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKED,
  GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL,
  GSHEET_WEEKLYPROMPT_COLUMN_STATE
)

"""
Class to manage discord bot utilities and functions.
"""
class DiscordBot(metaclass=Singleton):
  def __init__(self):
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    self.token = os.getenv(DISCORD_TOKEN)
    self.bot = discord.ext.commands.Bot(command_prefix='> ', intents=intents)
    self.approve_queue = {
      k: {} for k in ART_FIGHT_MODES
    }
    self.guild_name = os.getenv(DISCORD_GUILD)
    self.invite_links = {}
    self.extravaganza_invite_link = None
    self.players: dict[str, Player] = {}
    self.update_delay = 10
    self.players_df = None

  """
  Runs the bot.
  """
  def run(self):
    self.bot.run(self.token)

  """
  Some utilities are only accessible after the bot is running.
  Therefore, the remaining setup that is applicable will run in the ready hook.
  """
  def set_up_after_run(self):
    print("Generating map of members and uid...")

    self.guild = self.get_guild()
    self.df_discord_members = pd.DataFrame({
      "Discord": [i.name + "#" + str(i.discriminator) for i in self.guild.members],
      "uid" : [i.id for i in self.guild.members],
    })

    self.initialize_players_from_master_tracker()

  """
  From the master tracker sheet, populate the player information.
  """
  def initialize_players_from_master_tracker(self):
    df = get_player_from_gsheets()

    # Populate the unidentified discord members into the last worksheet.
    self.players_df = self.get_appended_unrecorded_members(df)

    self.initialize_players(self.players_df)

  def update_new_players(self):
    self.players_df = self.get_players_df_from_players()

    # Populate the unidentified discord members into the last worksheet.
    self.players_df = self.get_appended_unrecorded_members(self.players_df)

  def initialize_players(self, df):
    for index, row in df.iterrows():

      # set name as primary key because every member has it.
      key = row[GSHEET_COLUMN_NAME]

      if key in self.players.keys():
        print("DUPLICATE KEY ERROR ", key)

      self.players[key] = Player(row)

  def get_appended_unrecorded_members(self, df):
    self.df_discord_members = pd.DataFrame({
      "Discord": [i.name + "#" + str(i.discriminator) for i in self.guild.members],
      "uid" : [i.id for i in self.guild.members],
    })

    df[GSHEET_COLUMN_DISCORD_ID] = df[GSHEET_COLUMN_DISCORD].apply(lambda x: self.get_discord_handle(x) or '')
    #print(df[GSHEET_COLUMN_DISCORD_ID])
    list_of_recorded_members_discord_ids = df[GSHEET_COLUMN_DISCORD_ID].values.tolist()
    list_of_discord_members_discord_ids = self.df_discord_members["uid"].values.tolist()
    #print(list_of_recorded_members_discord_ids)
    #print(list_of_discord_members_discord_ids)

    # Find set of members who are not recorded in the form.
    set_of_unrecorded_members_discord_ids = set(list_of_discord_members_discord_ids) \
      - set(list_of_recorded_members_discord_ids)

    # Generates a dataframe of unrecorded members to the member list.
    src_unrecorded_members = list(map(
      lambda member_id: {
        **{k: '' for k in GSHEET_PLAYER_COLUMNS},
        # Set discord Id
        GSHEET_COLUMN_DISCORD_ID: str(member_id),
        # Set UUID as temp name. Must be unique.
        GSHEET_COLUMN_NAME: str(uuid.uuid4()),
        # Set messages data
        **{k: DEFAULT_MESSAGES_DATA for k in GSHEET_COLUMNS_MESSAGE_STATES},
        # Set scores
        GSHEET_INKTOBER_COLUMN_STATE: DEFAULT_INKTOBER_STATE_DATA,
        GSHEET_WEEKLYPROMPT_COLUMN_STATE: DEFAULT_WEEKLYPROMPT_STATE_DATA
      },
      list(set_of_unrecorded_members_discord_ids)
    ))

    df_unrecorded_members = pd.DataFrame(src_unrecorded_members)
    print(df.columns.sort_values())
    print(df_unrecorded_members.columns.sort_values())

    return pd.concat([df, df_unrecorded_members])


  """
  Stores player information back into the database.
  """

  def get_players_df_from_players(self): 
    dataframes = list(map(
      lambda player: pd.DataFrame(
        {k: [v] for k, v in player.export_to_df_row().items()}
      ),
      self.players.values()
    ))

    self.players_df = pd.concat(dataframes, axis=0)
    return self.players_df

  def update_players_to_db(self):
    self.get_players_df_from_players()
    update_columns_to_gsheets(
      input_df=self.players_df,
      doc_id=os.getenv(DOCID_MASTER_TRACKER),
      name_dict=None,
      column_names=GSHEET_PLAYER_COLUMNS
    )

  def task(self):
    df = get_player_from_gsheets()
    self.initialize_players(df)
    print("Launching Gsheet update task...")
    while True:
      # Crawls for new players to append to df
      self.update_new_players()

      # Update all player data to DB
      self.update_players_to_db()

      print("Gsheet updated")

      # Sleep
      time.sleep(self.update_delay)

  def get_guild(self, guild_name=None):
    #print(DISCORD_GUILD)
    if guild_name is None:
      guild_name = os.getenv(DISCORD_GUILD)
      print(guild_name) 

    filtered_guilds = \
      list(filter(
        lambda guild: guild.name == guild_name,
        self.bot.guilds
      ))

    return None if len(filtered_guilds) == 0 else filtered_guilds[0]

  def get_channel(self, guild, channel_name):
    # print(channel_name)
    if guild is None:
      guild = self.get_guild(os.getenv(DISCORD_GUILD))

    filtered_channels = list(filter(
      lambda channel: channel_name in channel.name,
      guild.channels
    ))

    return None if len(filtered_channels) == 0 else guild.get_channel(filtered_channels[0].id)

  def get_id_from_tag(self, tag):
    return tag[3:-1]


  async def get_msg_by_jump_url(self, ctx, channel, jump_url):

    guild = self.get_guild()
    channel = self.get_channel(guild, channel)

    if channel is None: 
      await ctx.send(
        "Channel not recognised. Make sure you spelt it right!"
      )
      return None

    messages = await channel.history(
      limit = DISCORD_MESSAGES_LIMIT,
    ).flatten()

    selected_message = list(filter(
      lambda message: message.jump_url == jump_url,
      messages
    ))[0]

    return selected_message

  def find_invite_by_code(self, invite_list, code):
    for inv in invite_list:
      if inv.code == code:
        return inv

  async def get_message_by_id(self, channel, id):
    return await channel.fetch_message(id)

  def get_discord_handle(self, discord_name, get_uid=True):

    df = self.df_discord_members
    # print(df)
    # print(discord_name)
    return get_fuzzily_discord_handle(discord_name, df, get_uid)

  def get_player_by_id(self, id):
    filtered_players = {k: v for k, v in self.players.items() if v.attributes(GSHEET_COLUMN_DISCORD_ID) == id}
    return list(filtered_players.items())[0][1]
