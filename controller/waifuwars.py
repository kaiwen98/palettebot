import os
import discord
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile
from config_loader import (
    ART_FIGHT_MODE_WAIFUWARS,
    ART_FIGHT_MODE_WAIFUWARS,
    ART_FIGHT_STATE,
    GUILD, 
    DELAY,
    WAIFUWARS_APPROVE_CHANNEL, 
    WAIFUWARS_RECEIVE_CHANNEL, 
    WAIFUWARS_REPORT_CHANNEL, 
    WAIFUWARS_APPROVE_CHANNEL,
    WAIFUWARS_RECEIVE_CHANNEL, 
    WAIFUWARS_REPORT_CHANNEL, 
    IS_HEROKU, 
    TOKEN, 
    call_stack,
    call_stack_waifuwars,
    bot,
)

import config_loader as cfg
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
    update_birthday_state_to_local_disk,
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
    get_channel, 
    get_day_from_message,
    get_msg_by_jump_url, 
    get_num_days_away, 
    get_rank_emoji, 
    get_timestamp_from_curr_datetime, 
    get_today_date,
    remove_messages
)


stuff_lock = asyncio.Lock()
call_stack_waifuwars = []

async def update_waifuwars(attacked_user, attacking_user, approve_request_to_service):
    _df_waifuwars = set_up_inktober()
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break
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




@bot.command(
    name='ww_getscores', 
    help='Get Drawtober scores'
)
async def get_scores_(ctx):
    print("here")
    await get_scores(True)
    
async def get_scores(command = False):
    print("LOOK!", cfg.curr_day, get_today_date(IS_HEROKU), datetime.now())
    if not command and (cfg.curr_day == get_today_date(IS_HEROKU)):
        return
    cfg.curr_day = get_today_date(IS_HEROKU)
    output = []
    rank = []
    _df = set_up_inktober()
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break
    _df_discord_members = pd.DataFrame({
        "Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
        "uid" : [i.id for i in guild.members],
        })
    print(_df_discord_members)

    output.append("**WAIFU-HUSBANDO WAR Scores!**\n")

    for index, row in _df.iterrows():
        try:

            if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members) is None:
                continue

            user_score_pair = (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members), row[WAIFUWARS_NUMATTACKING], row[WAIFUWARS_NUMATTACKED],)

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

    channel_to_send = "bot-spam" if command else WAIFUWARS_REPORT_CHANNEL
    await get_channel(bot, GUILD, channel_to_send).send(
        "**:art: :speaker: Your friendly WAIFU HUSBANDO WAR announcement!**\n%s\n" % ("https://discord.com/channels/668080486257786880/747465326748368947/757889890653306890") + "".join(output),
        file = discord.File(os.path.join(os.getcwd(), "PALETTE_INKTOBER.jpg"))
    )


async def on_message_waifuwars(message, approve_queue):
    print(bot.user.mentioned_in(message))
    global call_stack_waifuwars
    if message.channel.name == WAIFUWARS_RECEIVE_CHANNEL and \
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
                    message_approve_artwork = await get_channel(bot, GUILD, WAIFUWARS_APPROVE_CHANNEL).send(
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

                message_approve_artwork = await get_channel(bot, GUILD, WAIFUWARS_APPROVE_CHANNEL).send(
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

                # await get_channel(bot, GUILD, WAIFUWARS_RECEIVE_CHANNEL).send(
                #     "Received! <@%s>" % (message.author.id)
                # )

                clear_folder()

        else:
            await get_channel(bot, GUILD, WAIFUWARS_RECEIVE_CHANNEL).send(
                "You did not attach an artwork image!"
            )

    else:
        await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add_waifuwars(payload, approve_queue):
    message_approve_artwork_id = payload.message_id
    user = payload.member
    emoji = payload.emoji.name
    print(emoji)
    message_approve_artwork = await get_channel(bot, GUILD, WAIFUWARS_APPROVE_CHANNEL).fetch_message(message_approve_artwork_id)
    # print(message.id, type(message.id), list(approve_queue.keys()))

    if message_approve_artwork.id not in [i["message_approve_artwork"].id for i in approve_queue]:
        print(1)
        return

    # specifies the channel restriction
    if user.name not in ["okai_iwen", "tako", "Hoipus", approve_queue[-1]["attacked_user"].name]:
        print(2)
        return 

    if message_approve_artwork.channel.name != WAIFUWARS_APPROVE_CHANNEL:
        print(3)
        return

    approve_request_to_service = tuple(filter(lambda i: i["message_approve_artwork"].id == message_approve_artwork.id, approve_queue))[0]
    print(approve_request_to_service)
    attacking_user, attacked_user = approve_request_to_service["attacking_user"], approve_request_to_service["attacked_user"]
    message_artwork = approve_request_to_service["message_artwork"]
    approve_queue.remove(approve_request_to_service)

    print(approve_queue)

    if emoji == WAIFUWARS_CONCEDE_SIGN:
        await get_channel(bot, GUILD, WAIFUWARS_APPROVE_CHANNEL).send(
                    "**<@%s> conceded to this post!**:flag_white: :flag_white: :flag_white: \n**<@%s> won a WAIFU & HUSBANDO  WAR round! **:trophy: \n%s" % (user.id, message_artwork.author.id, message_artwork.jump_url),
                )
        await update_waifuwars(attacked_user, attacking_user, approve_request_to_service)

    await remove_messages([message_approve_artwork])



