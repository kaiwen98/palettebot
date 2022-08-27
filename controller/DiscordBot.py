from numpy import empty
from models.Singleton import Singleton
import discord
import discord.ext as d_ext
import os

class DiscordBot(metaclass=Singleton):
  def __init__(self):
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    self.token = os.getenv("DISCORD_TOKEN")
    print("asdasd", self.token)
    self.bot = discord.ext.commands.Bot(command_prefix='> ', intents=intents)
    self.approve_queue = []
    self.guild_name = os.getenv("DISCORD_GUILD")
    self.invite_links = {}
    self.extravaganza_invite_link = None

  def run(self):
    self.bot.run(self.token)

  def get_guild(self, guild_name):
    filtered_guilds = \
      list(filter(
        lambda guild: guild.name == self.guild_name,
        self.bot.guilds
      ))

    return None if len(filtered_guilds) == 0 else filtered_guilds[0]

  def get_channel(self, guild, channel_name):
    print(channel_name)
    filtered_channels = list(filter(
      lambda channel: channel_name in channel.name,
      guild.channels
    ))

    return None if len(filtered_channels) == 0 else guild.get_channel(filtered_channels[0].id)

