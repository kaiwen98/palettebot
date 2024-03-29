import os
import discord
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile
from config_loader import (
    ART_FIGHT_MODE_WAIFUWARS,
    ART_FIGHT_MODE_WAIFUWARS,
)

import config_loader as cfg
from models.DiscordBot import DiscordBot
from controller.gdrive_uploader import upload_to_gdrive
import asyncio
import pandas as pd
from discord.ext import commands

from controller.excelHandler import (
    INKTOBER_STATE,
    MEMBER_INFO_BIRTHDAY_STATE,
    MEMBER_INFO_COL_BDATE,
    MEMBER_INFO_COL_DISCORD,
    STATE_APPROVED,
    STATE_NO_SHOUTOUTS,
    STATE_SHOUTOUT_DAY,
    STATE_SHOUTOUT_WEEK,
    STATE_UNDER_APPROVAL,
    WAIFUWARS_NUMATTACKED,
    WAIFUWARS_NUMATTACKING,
    get_fuzzily_discord_handle, 
    pretty_print_social_handle_wrapper,
    set_up_inktober,
    set_up_member_info, 
    set_up_palette_particulars_csv,
    update_birthday_state_to_gsheets,
    update_inktober_state_to_gsheets, 
    verify_is_okay_to_share_by_discord_name
)
from controller.commons import get_list_of_artists
from controller.inktober import DICT_DAY_TO_PROMPT
from utils.commons import (
    APPROVE_SIGN,
    DIR_OUTPUT, 
    DISCORD_CHANNEL_ART_GALLERY, 
    DISCORD_MESSAGES_LIMIT,
    NOT_APPROVE_SIGN,
    WAIFUWARS_CONCEDE_SIGN
)
from utils.utils import (
    calculate_score, 
    clear_folder,
    get_attacked_user, 
    get_day_from_message,
    get_msg_by_jump_url, 
    get_num_days_away, 
    get_rank_emoji, 
    get_timestamp_from_curr_datetime, 
    get_today_date,
    remove_messages
)

async def update_waifuwars(attacked_user, attacking_user, approve_request_to_service):

    guild = DiscordBot().get_guild(None)
    _df_discord_members_attacked = pd.DataFrame({
        "Discord": [user.name + "#" + str(user.discriminator) for user in [attacked_user]],
        "uid" : [user.id for user in [attacked_user]],
    })
    _df_discord_members_attacking = pd.DataFrame({
        "Discord": [user.name + "#" + str(user.discriminator) for user in [attacking_user]],
        "uid" : [user.id for user in [attacking_user]],
    })

    current_attacked_score = update_waifu_wars_by_user(_df_waifuwars, _df_discord_members_attacked, WAIFUWARS_NUMATTACKED)
    current_attack_score = update_waifu_wars_by_user(_df_waifuwars, _df_discord_members_attacking, WAIFUWARS_NUMATTACKING)

    update_inktober_state_to_gsheets(_df_waifuwars)

def update_waifu_wars_by_user(df, ref_df, col):
    # iterates over the sheet
    # print(row[MEMBER_INFO_COL_DISCORD])
    print("hi")
    print(ref_df)
    for index, row in df.iterrows():
        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], ref_df, get_uid=True) is None:
            print("cant find %s %s" % (row[MEMBER_INFO_COL_DISCORD], ref_df))
            continue
        df.at[index, col] = str(int(row[col]) + 1)
        print("HEREEEEEEEEEEEE", df.at[index, col])
    return df.at[index, col]

async def waifuwars_task():
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if "bot-spam" in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    while True:
        # do something
        counter = DELAY
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
                    message_approve_artwork = await get_channel(bot, GUILD, os.getenv(WAIFUWARS_APPROVE_CHANNEL)).send(
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

                message_approve_artwork = await get_channel(bot, GUILD, os.getenv(WAIFUWARS_APPROVE_CHANNEL)).send(
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
            await get_channel(bot, GUILD, os.getenv(WAIFUWARS_RECEIVE_CHANNEL)).send(
                "You did not attach an artwork image!"
            )

    else:
        await bot.process_commands(message)

async def get_scores(command = False):
    print("LOOK!", cfg.curr_day, get_today_date(), datetime.now())
    if not command and (cfg.curr_day == get_today_date()):
        return
    cfg.curr_day = get_today_date()
    output = []
    rank = []
    df_waifuwars = set_up_inktober()
    guild = DiscordBot().get_guild(GUILD)
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

            if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members) is None:
                continue

            user_score_pair = (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], df_discord_members), row[WAIFUWARS_NUMATTACKING], row[WAIFUWARS_NUMATTACKED],)

            if int(row[WAIFUWARS_NUMATTACKING]) > 0:
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

    await get_channel(bot, GUILD, channel_to_send).send(
        "**:art: :speaker: Your friendly WAIFU HUSBANDO WAR announcement!**\n%s\n" % ("https://discord.com/channels/668080486257786880/747465326748368947/757889890653306890") + "".join(output),
        file = discord.File(os.path.join(os.getcwd(), "PALETTE_INKTOBER.jpg"))
    )





