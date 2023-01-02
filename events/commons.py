"""
Consolidates all commands that is related to the birthdayTracker.
"""
import controller
from models.DiscordBot import DiscordBot
from controller import inktober as ink
from controller import waifuwars as waf
from controller import weeklyprompts as weekp
from controller import birthdayTracker

import asyncio
from controller.commons import (
	get_photos,
	get_all_members_text
)
from controller.excelHandler import (
	get_fuzzily_discord_handle,
	set_up_member_info,
	set_up_palette_particulars_csv,
	update_birthday_state_to_gsheets
)

import controller.excelHandler as exc
from config_loader import (
	ART_FIGHT_MODE_INKTOBER,
	ART_FIGHT_MODE_WAIFUWARS,
	get_config_param,
	set_config_param,
)
from utils.constants import (
	ART_FIGHT_MODE_WEEKLY_PROMPTS, 
	ART_FIGHT_STATE, 
	BOT_USERNAME, 
	DISCORD_GUILD,
	EXTRAVAGANZA_ROLE, 
	WEEKLYPROMPTS_RECEIVE_CHANNEL
)

from utils.utils import (
	get_day_from_message,
	get_num_days_away,
	get_today_datetime,
)

import datetime

import pandas as pd

import re

import config_loader as cfg
import os


def register_events():

	bot = DiscordBot().bot
	@bot.event
	async def on_ready():
		print(os.getenv(WEEKLYPROMPTS_RECEIVE_CHANNEL))
		links = await DiscordBot().get_guild().invites()
		f_links = list(filter(lambda link: link.code in ['WbGacQnYUp'], links))
		#print(f_links[0].uses)
		#print(links)
		members = DiscordBot().get_guild().members
		f_members = \
			list(filter(lambda member: \
				"Member" not in member.roles \
				and member.joined_at >= datetime.datetime(2022, 2, 1, 0, 0, 0)
				and member.joined_at <= datetime.datetime(2022, 6, 1, 0, 0, 0)
			   , members))
		f_members.sort(key=lambda x: x.joined_at)

		print(list(map(lambda x: [x.name, x.nick], f_members)))
		print(f_members)
		await DiscordBot().set_up_after_run()
		print("[INFO] Ready!")
		await DiscordBot().bot.user.edit(username=os.getenv(BOT_USERNAME))
			
		print(f'{bot.user} has connected to Discord!')



		print(links)

		if get_config_param(ART_FIGHT_STATE) == ART_FIGHT_MODE_INKTOBER:
			bot.loop.create_task(ink.task())
		elif get_config_param(ART_FIGHT_STATE) == ART_FIGHT_MODE_WAIFUWARS:
			bot.loop.create_task(waf.task())
		elif get_config_param(ART_FIGHT_STATE) == ART_FIGHT_MODE_WEEKLY_PROMPTS:
			bot.loop.create_task(weekp.task())
		
		# This periodic task is pretty wasteful.
		# Should just run a refresh by command only when required.
		# bot.loop.create_task(DiscordBot().task())
		# bot.loop.create_task(birthdayTracker.task())


	@bot.command(
		name='get_sys_datetime',
		help='Help to print system datetime for debugging.'
	)
	async def get_sys_datetime(ctx):
		await ctx.send(f"```{get_today_datetime()}```")

	@bot.command(
		name='sync',
		help='Synchronise with google sheet'
	)
	async def sync(ctx):
		await ctx.send(f"```Syncing...```")
		await DiscordBot().sync_db()
		await ctx.send(f"```Done!```")

	@bot.command(
		name="msg",
		help="Relay message as Palettebot"
	)
	async def msg(ctx, channel_name):
		channel = DiscordBot().get_channel(None, channel_name)
		return await channel.send(re.sub(r">\s+msg\s+.*\s+", "", ctx.message.content))



	@bot.command(
		name='export', 
		help='Provide \"export DD MM DD MM YYYY\", with start date first and end date last. The year is optional, so no entry means current year.'
	)
	async def export(ctx, channel: str, dd_begin: int, mm_begin: int, dd_end: int, mm_end: int, year=None):
		global df

		#print(",", year, ",")

		if year is None:
			year = datetime.datetime.today().year

			palette_particulars = set_up_palette_particulars_csv()
			await ctx.send(
				"```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
			)
			#try:
			await get_photos(channel, palette_particulars, dd_begin, mm_begin, dd_end, mm_end, year, ctx)
			# except Exception as e:
			# await ctx.send(
			# "```Error occured! Contact the administrator. Message: %s```" % (str(e))
			# )

	@bot.command(
		name='getallmembers', 
		help='Provide \"getallmembers VOICECHANNEL\", Outputs a list of members in a specified voice chat.'
	)
	async def get_all_members(ctx, channel: str):
		palette_particulars = set_up_palette_particulars_csv()
		await ctx.send(
			"```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
		)
		try:
			await get_all_members_text(channel, ctx)
		except Exception as e:
			await ctx.send(
				"```Error occured! Contact the administrator. Message: %s```" % (str(e))
			)

	@bot.command(
		name='ex2022_kick_participants', 
		help='Kick all participants with the role: Extravaganza 2022 Participant'
	)
	async def ex2020_kick_participants(ctx):
		guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
		for member in guild.members:
			if ( 
				len(list(filter(lambda role: role.name == EXTRAVAGANZA_ROLE, member.roles))) > 0 \
				and len(list(filter(lambda role: role.name == 'Member', member.roles))) == 0
			):
				print("kick: ", member.name)
				await guild.kick(member, reason = "Thank you for joining our NUSCAS Palette Discord! Hope it has been fun for you :)") 

	@bot.command(
		name='ex2022_set_new_invite', 
		help='Set a new invite link. If no link is provided, a new one is generated.'
	)
	async def ex2020_set_new_invite(ctx, updated_invite = None):
		guild = DiscordBot().get_guild(GUILD)
		link = None
		invites = await guild.invites()

		if updated_invite is None:
			channel = DiscordBot().get_channel(guild, "general")
			link = channel.create_invite()
			link = link.code

		else:
			for i in invites:
				if i.code == updated_invite:
					link = i.code
					break

			if link is not None:
				await ctx.send(
					"```Your updated invite link is https://discord.gg/%s```" % (link)
				)

				if DiscordBot().extravaganza_invite_link is not None:

					tmp = DiscordBot().find_invite_by_code(invites, DiscordBot().extravaganza_invite_link)
					if tmp is not None:
						await tmp.delete()

					DiscordBot().extravaganza_invite_link = link
					print(DiscordBot().extravaganza_invite_link, " is created")

			else:
				await ctx.send(
					"```We cannot find the link. It is invalid.```"
				)    

			DiscordBot().invite_links[guild.id] = await guild.invites()




