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
    self.bot = discord.ext.commands.Bot(command_prefix='> ', intents=intents)
    self.approve_queue = []
    self.invite_links = []
    self.extravaganza_invite_link = None

  def run(self):
    self.bot.run(self.token)

  def get_guild(self, guild_name):
    return list(filter(
      lambda guild: guild.name == guild_name,
      self.bot.guilds
    ))[0]

  def get_channel(self, guild, channel_name):
    channel = list(filter(
      lambda channel: channel.name == channel_name,
      guild.channels
    ))[0]

    return guild.get_channel(channel.id)

