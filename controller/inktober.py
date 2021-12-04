from datetime import datetime
import os
import discord
import pandas as pd
import requests
import asyncio
from config_loader import GUILD, INKTOBER_APPROVE_CHANNEL, INKTOBER_RECEIVE_CHANNEL, INKTOBER_REPORT_CHANNEL, IS_HEROKU, bot, DELAY
import config_loader as cfg
from controller.excelHandler import INKTOBER_STATE, MEMBER_INFO_COL_DISCORD, STATE_APPROVED, STATE_UNDER_APPROVAL, get_fuzzily_discord_handle, set_up_inktober, update_inktober_state_to_gsheets
from utils.commons import APPROVE_SIGN, DIR_OUTPUT, NOT_APPROVE_SIGN
from utils.utils import calculate_score, clear_folder, get_channel, get_day, get_rank_emoji, get_today_date, remove_messages


DICT_DAY_TO_PROMPT = {
    1: "Cactus",
    2: "Pitcher Plant",
    3: "Climbing Plant",
    4: "Flowers",
    5: "Seedling",
    6: "Terrarium",
    7: "Forest",
    8: "Mushroom",
    9: "Venus Flytrap",
    10: "Rafflesia",
    11: "Dinner",
    12: "Void Deck",
    13: "Coffeeshop",
    14: "Playground",
    15: "Working from Home",
    16: "Ice-cream",
    17: "Bus/Train",
    18: "Rain",
    19: "Park",
    20: "Convenience Store",
    21: "Witch",
    22: "Skull",
    23: "Haunted",
    24: "Grave",
    25: "Vampire",
    26: "Candles",
    27: "Bats",
    28: "Bugs",
    29: "Classroom",
    30: "Dolls",
    31: "Your Worst Fear"
}

async def inktober_task():
    counter = 0
    channel_to_send = INKTOBER_REPORT_CHANNEL
    await get_channel(bot, GUILD, channel_to_send).send(
        "**Hope you all have enjoyed Palettober! I will stop the reminder messages from here on. \nWe will have more things coming our way so stay tuned uwu**",
        file = discord.File(os.path.join(os.getcwd(), "happy.png"))
    )
    while True:
        # do something

        continue
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
    if get_today_date(IS_HEROKU) < 11: 
        prompt_type = ":potted_plant:"
    elif get_today_date(IS_HEROKU) < 21:
        prompt_type = ":house:"
    else:
        prompt_type = ":ghost:"
    output.append(
        "Good Morning! Today's Palette Drawtober prompt is ... %s **%s**!\n\n" % (prompt_type, DICT_DAY_TO_PROMPT[get_today_date(IS_HEROKU)])
    )

    output.append("**Drawtober Scores!**\n")

    for index, row in _df.iterrows():
        try:

            if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members) is None:
                continue

            user_score_pair = (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members), calculate_score(row[INKTOBER_STATE]))

            if str(STATE_APPROVED) in list(row[INKTOBER_STATE]):
                rank.append(user_score_pair)

        except Exception as e:
            continue

    rank.sort(key = lambda tup: tup[1], reverse = True)

    for index, _user_score_pair in enumerate(rank):
        output.append("Rank %s %s .... **%s** [Score: %s]\n" % (
            index + 1,
            get_rank_emoji(index + 1),
            _user_score_pair[0], 
            _user_score_pair[1],
            )
        )
    
    if len(rank) == 0:
        output.append("No submissions yet.. Draw something!")

    channel_to_send = "bot-spam" if command else INKTOBER_REPORT_CHANNEL
    await get_channel(bot, GUILD, channel_to_send).send(
        "**:art: :speaker: Your friendly DRAWTOBER announcement!**\n%s\n" % ("https://discord.com/channels/668080486257786880/747465326748368947/893389786667163659") + "".join(output),
        file = discord.File(os.path.join(os.getcwd(), "PALETTE_INKTOBER.jpg"))
    )

async def update_inktober(user, state, date):
    _df_inktober = set_up_inktober()
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break
    _df_discord_members = pd.DataFrame({
        "Discord": [user.name + "#" + str(user.discriminator)],
        "uid" : [user.id],
        })
    print(_df_discord_members)

    for index, row in _df_inktober.iterrows():
        # iterates over the sheet
        # print(row[MEMBER_INFO_COL_DISCORD])
        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members, get_uid=True) is None:
            continue
        

        state_ls = list(row[INKTOBER_STATE])
        state_ls[date] = str(state)
        _df_inktober.at[index, INKTOBER_STATE] = "".join(state_ls)
        # print("HEREEEEEEEEEEEE", _df_inktober.at[index, INKTOBER_STATE])
    update_inktober_state_to_gsheets(_df_inktober)


async def on_message_inktober(message, approve_queue):
    print(bot.user.mentioned_in(message))
    if message.channel.name == INKTOBER_RECEIVE_CHANNEL and \
        bot.user.mentioned_in(message) and \
        message.author != bot.user:
        
        print("TEXT: ", message.content)
        day_to_approve = get_day(message)

        if "io" not in os.listdir(os.getcwd()):
            os.mkdir(DIR_OUTPUT)
        print("there")
        if len(message.attachments) > 0 :

            response = requests.get(message.attachments[0].url)

            filename = "io/%s.%s" % (
                "tmp",
                str(message.attachments[0].url).split(".")[-1]
                )

            with open(filename, "wb") as f:
                f.write(response.content)

            message_approve_artwork = await get_channel(bot, GUILD, INKTOBER_APPROVE_CHANNEL).send(
                "Theme: %s. \nApprove this post? %s" % (DICT_DAY_TO_PROMPT[day_to_approve], message.jump_url),
                file = discord.File(os.path.join(os.getcwd(), filename))
            )

            await update_inktober(message.author, STATE_UNDER_APPROVAL, day_to_approve - 1)

            approve_queue.append({
                "type" : "inktober",
                "day" : day_to_approve, 
                "message_artwork" : message, 
                "message_approve_artwork" : message_approve_artwork
            })

            await message_approve_artwork.add_reaction(APPROVE_SIGN)
            await message_approve_artwork.add_reaction(NOT_APPROVE_SIGN)

            await get_channel(bot, GUILD, INKTOBER_RECEIVE_CHANNEL).send(
                "Received! <@%s>" % (message.author.id)
            )

            clear_folder()
        else:
            await get_channel(bot, GUILD, INKTOBER_RECEIVE_CHANNEL).send(
                "You did not attach an artwork image!"
            )

    else:
        await bot.process_commands(message)

async def on_raw_reaction_add_inktober(payload, approve_queue):
    message_approve_artwork_id = payload.message_id
    user = payload.member
    emoji = payload.emoji.name
    print(emoji)
    message_approve_artwork = await get_channel(bot, GUILD, INKTOBER_APPROVE_CHANNEL).fetch_message(message_approve_artwork_id)

    # print(message.id, type(message.id), list(approve_queue.keys()))
    if message_approve_artwork.id not in [i["message_approve_artwork"].id for i in approve_queue]:
        return


    # specifies the channel restriction
    if user.name not in ["okai_iwen", "tako", "Hoipus"]:
        return 

    if message_approve_artwork.channel.name != INKTOBER_APPROVE_CHANNEL:
        return

    approve_request_to_service = tuple(filter(lambda i: i["message_approve_artwork"].id == message_approve_artwork.id, approve_queue))[0]
    day = approve_request_to_service["day"]
    message_artwork = approve_request_to_service["message_artwork"]
    approve_queue.remove(approve_request_to_service)

    print(approve_queue)

    if emoji == APPROVE_SIGN:
        await get_channel(bot, GUILD, INKTOBER_APPROVE_CHANNEL).send(
                    "> <@%s> approved this post: %s" % (user.id, message_artwork.jump_url),
                )
        await update_inktober(message_artwork.author, STATE_APPROVED, day - 1)

    elif emoji == NOT_APPROVE_SIGN:
        await get_channel(bot, GUILD, INKTOBER_APPROVE_CHANNEL).send(
                    "> <@%s> rejected this post: %s" % (user.id, message_artwork.jump_url),
                )
        await get_channel(bot, GUILD, INKTOBER_RECEIVE_CHANNEL).send(
                    "> <@%s> Due to some reasons, your post is not accepted! Sorry... %s" % (message_artwork.author.id, message_artwork.jump_url),
                )
    await remove_messages([message_approve_artwork])
