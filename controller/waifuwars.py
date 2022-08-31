import os
import discord
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile
from config_loader import (
	ART_FIGHT_MODE_WAIFUWARS,
	ART_FIGHT_MODE_WAIFUWARS,
	get_recorded_date,
	set_recorded_date,
)

import config_loader as cfg
from models.DiscordBot import DiscordBot
from controller.gdrive_uploader import upload_to_gdrive
import asyncio
import pandas as pd
from discord.ext import commands

from controller.excelHandler import (
	get_fuzzily_discord_handle, 
	pretty_print_social_handle_wrapper,
	set_up_inktober,
	set_up_member_info, 
	set_up_palette_particulars_csv,
	set_up_waifuwars,
	update_birthday_state_to_gsheets,
	update_inktober_state_to_gsheets, 
	verify_is_okay_to_share_by_discord_name
)
from controller.commons import get_list_of_artists
from controller.inktober import DICT_DAY_TO_PROMPT
from utils.commons import (
	APPROVE_SIGN,
	DELAY,
	DIR_OUTPUT, 
	DISCORD_CHANNEL_ART_GALLERY,
	DISCORD_CHANNEL_WAIFU_WARS,
	DISCORD_GUILD, 
	DISCORD_MESSAGES_LIMIT,
	GSHEET_COLUMN_DISCORD,
	GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKED,
	GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKING,
	NOT_APPROVE_SIGN,
	WAIFUWARS_APPROVE_CHANNEL,
	WAIFUWARS_CONCEDE_SIGN,
	WAIFUWARS_RECEIVE_CHANNEL,
	WAIFUWARS_REPORT_CHANNEL
)
from utils.utils import (
	calculate_score, 
	clear_folder,
	get_day_from_message,
	get_num_days_away, 
	get_rank_emoji, 
	get_timestamp_from_curr_datetime, 
	get_today_date,
	remove_messages
)

async def update_waifuwars(attacked_user, attacking_user, approve_request_to_service):
	df_waifuwars = set_up_waifuwars()
	guild = DiscordBot().get_guild(None)
	_df_discord_members_attacked = pd.DataFrame({
		"Discord": [user.name + "#" + str(user.discriminator) for user in [attacked_user]],
		"uid" : [user.id for user in [attacked_user]],
	})
	_df_discord_members_attacking = pd.DataFrame({
		"Discord": [user.name + "#" + str(user.discriminator) for user in [attacking_user]],
		"uid" : [user.id for user in [attacking_user]],
	})

	current_attacked_score = update_waifu_wars_by_user(df_waifuwars, _df_discord_members_attacked, GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKED)
	current_attack_score = update_waifu_wars_by_user(df_waifuwars, _df_discord_members_attacking, GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKING)

	update_inktober_state_to_gsheets(df_waifuwars)

def update_waifu_wars_by_user(df, ref_df, col):
	# iterates over the sheet
	# print(row[MEMBER_INFO_COL_DISCORD])
	print("hi")
	print(ref_df)
	for index, row in df.iterrows():
		if get_fuzzily_discord_handle(row[GSHEET_COLUMN_DISCORD], ref_df, get_uid=True) is None:
			print("cant find %s %s" % (row[GSHEET_COLUMN_DISCORD], ref_df))
			continue
		df.at[index, col] = str(int(row[col]) + 1)
		print("HEREEEEEEEEEEEE", df.at[index, col])
		return df.at[index, col]

async def waifuwars_task():
		DiscordBot().get_channel(None, os.getenv(WAIFUWARS_REPORT_CHANNEL))
		while True:
			# do something
			counter = int(os.getenv(DELAY))
			# try:
			await get_scores()
			# except Exception as e:
			#     await channel.send(
			#         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
			#     )

			while counter > 0:
				counter = counter - 1
				await asyncio.sleep(1)

async def on_message_waifuwars(message, approve_queue):
	bot = DiscordBot().bot
	print(bot.user.mentioned_in(message))
	global call_stack_waifuwars
	if message.channel.name == os.getenv(WAIFUWARS_RECEIVE_CHANNEL) and \
			bot.user.mentioned_in(message) and \
			message.author != bot.user:

		print("TEXT: ", message.content)

		if "io" not in os.listdir(os.getcwd()):
			os.mkdir(DIR_OUTPUT)
			print("there")
			if len(message.attachments) > 0 :


				messages_ref_artwork = await get_attacked_user(message)
				print(messages_ref_artwork)

				for message_ref_artwork in messages_ref_artwork:
					if message_ref_artwork.author.id == message.author.id and message.author.name != "okai_iwen":
						message_approve_artwork = await DiscordBot().get_channel(None, os.getenv(WAIFUWARS_APPROVE_CHANNEL)).send(
							content = "**Silly, you can't attack yourself!**" 
						)
						return
					response = requests.get(message_ref_artwork.attachments[0].url)
					print(message_ref_artwork.attachments)
					print(str(message_ref_artwork.attachments[0].url))
					filename = "io/%s.%s" % (
						"tmp",
						str(message_ref_artwork.attachments[0].url).split(".")[-1]
					)

					with open(filename, "wb") as f:
						f.write(response.content)

						message_approve_artwork = await DiscordBot().get_channel(None, os.getenv(WAIFUWARS_APPROVE_CHANNEL)).send(
							content = "**<@%s> is attacked!** :gun: :gun: :gun: .\n:princess: :prince: Your waifu/husbando is <%s>!\n:crossed_swords: :crossed_swords: Attacker assaulted from <%s>!\n**Do you concede :flag_white: :flag_white: :flag_white:?**" % \
							(message_ref_artwork.author.id, message_ref_artwork.jump_url, message.jump_url),
							file = discord.File(os.path.join(os.getcwd(), filename)),
							embed = None
						)

						approve_queue.append({
							"type" : "waifuwars",
							"attacking_user": message.author, 
							"attacked_user" : message_ref_artwork.author,
							"message_approve_artwork" : message_approve_artwork,
							"message_artwork" : message,
							"message_ref_artwork" : message_ref_artwork,
						})

						await message_approve_artwork.add_reaction(WAIFUWARS_CONCEDE_SIGN)

						# await get_channel(bot, GUILD, os.getenv(WAIFUWARS_RECEIVE_CHANNEL)).send(
						#     "Received! <@%s>" % (message.author.id)
						# )

						clear_folder()

				else:
					await DiscordBot().get_channel(None, os.getenv(WAIFUWARS_RECEIVE_CHANNEL)).send(
						"You did not attach an artwork image!"
					)

		else:
			await bot.process_commands(message)

async def get_scores(command = False):
	if not command and (get_recorded_date() == get_today_date()):
		return
	set_recorded_date(get_today_date())
	output = []
	rank = []
	df_waifuwars = set_up_inktober()
	guild = DiscordBot().get_guild(os.getenv(DISCORD_GUILD))
	channel_to_send = DiscordBot().get_channel(
		guild, 
		"bot-spam" if command else os.getenv(WAIFUWARS_REPORT_CHANNEL)
	)

	df_discord_members = pd.DataFrame({
		"Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
		"uid" : [i.id for i in guild.members],
	})
	print(df_discord_members)

	output.append("**WAIFU-HUSBANDO WAR Scores!**\n")

	for index, row in df_waifuwars.iterrows():
		try:

			if get_fuzzily_discord_handle(row[GSHEET_COLUMN_DISCORD], df_discord_members) is None:
				continue

			user_score_pair = (
				get_fuzzily_discord_handle(row[GSHEET_COLUMN_DISCORD], df_discord_members), 
				row[GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKING], 
				row[GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKED]
			)

			if int(row[GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKING]) > 0:
				rank.append(user_score_pair)

		except Exception as e:
			continue

		rank.sort(key = lambda tup: tup[1], reverse = True)

		for index, _user_score_pair in enumerate(rank):
			output.append("Rank %s %s .... **%s** [:dagger: **%s**] [:ambulance: **%s**]\n" % (
				index + 1,
				get_rank_emoji(index + 1),
				_user_score_pair[0], 
				_user_score_pair[1],
				_user_score_pair[2],
			)
								 )

		if len(rank) == 0:
			output.append("No submissions yet.. Draw something!")

		await DiscordBot().get_channel(guild, channel_to_send).send(
			"**:art: :speaker: Your friendly WAIFU HUSBANDO WAR announcement!**\n%s\n" % ("https://discord.com/channels/668080486257786880/747465326748368947/757889890653306890") + "".join(output),
			file = discord.File(os.path.join(os.getcwd(), "PALETTE_INKTOBER.jpg"))
		)

async def get_attacked_user(message):
	output = []
	bot = DiscordBot().bot
	if len(message.content.strip().split(" ")) >= 2:
		tags = message.content.strip().split(" ", 1)[1]
		print(tags)
		messages = await DiscordBot().get_channel(None, os.getenv(DISCORD_CHANNEL_WAIFU_WARS)).history(
			limit = DISCORD_MESSAGES_LIMIT,
		).flatten()
		for tag in tags.strip().split(" "):
			id = DiscordBot().get_id_from_tag(tag)
			tmp = await get_waifu_of_user(id, messages)
			output.append(tmp)
			print(output)
		return output

async def get_waifu_of_user(id, messages = None):
	print(id)
	if messages is None:
		messages = await DiscordBot().get_channel(None, os.getenv(DISCORD_CHANNEL_WAIFU_WARS)).history(
			limit = DISCORD_MESSAGES_LIMIT,
		).flatten()
		for message in messages: 
			# print(id, message.author.id, message.content)
			if message.author.id == int(id.strip()) and len(message.attachments) > 0:
				return message



