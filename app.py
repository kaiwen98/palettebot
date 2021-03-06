import code
import os
import discord
from discord.ext import commands
from discord.utils import get
import requests
from datetime import datetime, time, timedelta
from zipfile import ZipFile
from config_loader import (
    ART_FIGHT_MODE_INKTOBER,
    ART_FIGHT_MODE_WAIFUWARS,
    ART_FIGHT_STATE,
    GUILD, 
    DELAY,
    BIRTHDAY_REPORT_CHANNEL,
    INKTOBER_APPROVE_CHANNEL, 
    INKTOBER_RECEIVE_CHANNEL, 
    INKTOBER_REPORT_CHANNEL, 
    WAIFUWARS_APPROVE_CHANNEL,
    WAIFUWARS_RECEIVE_CHANNEL, 
    WAIFUWARS_REPORT_CHANNEL, 
    IS_HEROKU, 
    TOKEN, 
    call_stack,
    bot, 
)
import config_loader as cfg
from controller.gdrive_uploader import upload_to_gdrive
import asyncio
import pandas as pd
from controller.inktober import DICT_DAY_TO_PROMPT
from controller import inktober as ink
from controller import waifuwars as waf


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
from controller.get_list_of_artists import get_list_of_artists
from utils.commons import (
    DIR_OUTPUT, 
    DISCORD_CHANNEL_ART_GALLERY, 
    DISCORD_MESSAGES_LIMIT,
    EXTRAVAGANZA_ROLE,
    MEMBER_ROLE
)
from utils.utils import (
    calculate_score, 
    clear_folder, 
    get_channel, 
    get_day,
    get_guild,
    get_msg_by_jump_url, 
    get_num_days_away, 
    get_rank_emoji, 
    get_timestamp_from_curr_datetime, 
    get_today_date, 
    remove_messages
)

stuff_lock = asyncio.Lock()

repeat_dict = {}
approve_queue = []

member_to_approve = None
counter: int
df = None

export_file: str

invite_links = {}

EXTRAVAGANZA_INVITE_LINK = 'ddekPqAckv'

async def _get_all_members(channel_input, ctx):
    channel = None
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if channel_input in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    if channel is None: 
        await ctx.send(
            "Channel not recognised. Make sure you spelt it r_ight!"
        )
        return

    members = channel.members #finds members connected to the channel

    mem_names = [] #(list)
    for member in members:
        mem_names.append(member.name + "\n")

    await ctx.send(
        "".join(mem_names)
    )

async def get_photos(channel_input, dd_begin, mm_begin, dd_end, mm_end, year, ctx): 
    """
        The code should look back to a large number of messages within a particular date range,
        Then downloads all images from artists who have the right permissions.

        TODO: Relocate this code to controller/artwork_extract.py 
    """

    global export_file
    channel = None
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if channel_input in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    if channel is None: 
        await ctx.send(
            "Channel not recognised. Make sure you spelt it right!"
        )
        return

    messages = await channel.history(
        limit = DISCORD_MESSAGES_LIMIT,
        ).flatten()

    folder_name = get_timestamp_from_curr_datetime()
    if "io" not in os.listdir(os.getcwd()):
        os.mkdir(DIR_OUTPUT)
    os.mkdir(os.path.join(DIR_OUTPUT, folder_name))

    for message in messages: 
        print(message.author)
        print(message.content)
        print(message.attachments)
        print(message.created_at)

        if str(message.author) not in repeat_dict.keys():
            repeat_dict[str(message.author)] = 0
        # Startline
        if (message.created_at < datetime(year, mm_begin, dd_begin, 0, 0, 0) - timedelta(hours = 8)): 
            print("Done!")
            break
        # Deadline
        elif (message.created_at > datetime(year, mm_end, dd_end, 0, 0, 0) - timedelta(hours = 8)): 
            continue

        if len(message.attachments) > 0:

                
            if get_fuzzily_discord_handle(str(message.author), df) is None or not verify_is_okay_to_share_by_discord_name(str(message.author), df):
                print(message.author, " do not wish to share")
                continue
            response = requests.get(message.attachments[0].url)
            filename = "io/%s/%s.%s" % (
                folder_name, 
                pretty_print_social_handle_wrapper(name = str(message.author), df = df),
                str(message.attachments[0].url).split(".")[-1]
                )
            if repeat_dict[str(message.author)] >= 1:
                print("file exists")
                filename = "io/%s/%s.%s" % (
                    folder_name, 
                    pretty_print_social_handle_wrapper(name = str(message.author), df = df) + "_%s" % (repeat_dict[str(message.author)]),
                    str(message.attachments[0].url).split(".")[-1]
                    )

            with open(filename, "wb") as f:
                repeat_dict[str(message.author)] = repeat_dict[str(message.author)] + 1 
                f.write(response.content)
    

    zip_name = "io/%s.zip" % (folder_name)
    zipFile = ZipFile(zip_name, 'w')
  
    curr_dir = os.path.join(os.getcwd(), "io", folder_name)
    await ctx.send(
        get_list_of_artists(curr_dir)
    )
    print(curr_dir)
    for file in os.listdir(curr_dir):
        print(os.path.join(curr_dir, file))
        zipFile.write(os.path.join(curr_dir, file), file)
    zipFile.close()
    await ctx.send(
        "Log in to Palette Exco Email to access the ZIP file! Link: %s" %
        upload_to_gdrive([zip_name])
    )

    clear_folder()
        

async def update_inktober(user, state, date):
    """
        The code should update state to excel sheet.

        TODO: Relocate this code to controller/inktober.py 
    """
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
        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members, get_uid=True) is None:
            continue
        

        state_ls = list(row[INKTOBER_STATE])
        state_ls[date] = str(state)
        _df_inktober.at[index, INKTOBER_STATE] = "".join(state_ls)
    update_inktober_state_to_gsheets(_df_inktober)

async def handle_check_birthdates_and_give_shoutout():
    """
        The code should handle birthday logic.

        TODO: Relocate this code to controller/birthday.py 
    """
    flag = False
    sent_bday_pic = False
    sent_week_pic = False
    _df = set_up_member_info()
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break
    _df_discord_members = pd.DataFrame({
        "Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
        "uid" : [i.id for i in guild.members],
        })
    print(_df_discord_members)

    for g_channel in guild.channels:
        if BIRTHDAY_REPORT_CHANNEL in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    for index, row in _df.iterrows():
        if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members, get_uid=True) is None:
            continue
        
        try:
            if get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) == 0 and \
                (int(row[MEMBER_INFO_BIRTHDAY_STATE]) & STATE_SHOUTOUT_DAY == 0):
                # Birthday is today,

                if sent_bday_pic is False:
                    await channel.send(
                        file = discord.File(os.path.join(os.getcwd(), "cake_day.gif"))
                    )  

                    sent_bday_pic = True

                await channel.send(
                    "Birthday baby sighted! :mag_right: :mag_right: HAPPY BIRTHDAY <@%s> :birthday: :candle: :birthday: :candle:" % \
                        (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members, get_uid=True)),
                )  

                _df.at[index, MEMBER_INFO_BIRTHDAY_STATE] = int(row[MEMBER_INFO_BIRTHDAY_STATE]) | STATE_SHOUTOUT_DAY
                flag = True

            elif get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) <= 7 and \
                get_num_days_away(row[MEMBER_INFO_COL_BDATE].date()) > 0 and \
                (int(row[MEMBER_INFO_BIRTHDAY_STATE]) & STATE_SHOUTOUT_WEEK == 0):
                # Birthday is a week away,
                if sent_week_pic is False:
                    await channel.send(
                        file = discord.File(os.path.join(os.getcwd(), "cake_is_a_lie.jpg"))
                    )  
                    sent_week_pic = True

                await channel.send(
                    "<@%s> 's birthday is less than a week away! Are yall excited :))) :eyes: :eyes: :eyes:" % \
                        (get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members, get_uid=True)),
                )  
                _df.at[index, MEMBER_INFO_BIRTHDAY_STATE] = int(row[MEMBER_INFO_BIRTHDAY_STATE]) | STATE_SHOUTOUT_WEEK
                flag = True

            elif datetime.now().day == 1 and datetime.now().month == 1:
                _df[MEMBER_INFO_BIRTHDAY_STATE] = [STATE_NO_SHOUTOUTS for i in range(_df.shape[0])]
        except:
            print("Date not valid.")
    if flag is False:
        pass
    print(_df)
    update_birthday_state_to_gsheets(_df)
        
async def birthday_task():
    """
        Entry point to birthday logic. 
        TODO: Relocate this code to controller/birthday.py 
    """
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
        await handle_check_birthdates_and_give_shoutout()
        # except Exception as e:
        #     await channel.send(
        #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
        #     )

        while counter > 0:
                counter = counter - 1
                await asyncio.sleep(1)

"""
    Command Handlers    
"""

@bot.command(
    name='bd_setdelay', 
    help='Change birthday delay in seconds.'
)
async def change_bd_delay(ctx, delay):
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if "bot-spam" in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break
    if int(delay) < 0: 
        await channel.send("Counter value: %d" % (counter))
    else:
        cfg.DELAY = int(delay)
        await channel.send(
            "```Delay Change Complete!```"
            )

@bot.command(
    name='bd_listmonth', 
    help='Get all birthdays for the month'
)
async def get_month_birthdays(ctx):
    output = []
    _df = set_up_member_info()
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break
    _df_discord_members = pd.DataFrame({
        "Discord": [i.name + "#" + str(i.discriminator) for i in guild.members],
        "uid" : [i.id for i in guild.members],
        })
    print(_df_discord_members)

    for g_channel in guild.channels:
        if "bot-spam" in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    for index, row in _df.iterrows():
        try:

            if get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members) is None:
                continue

            if row[MEMBER_INFO_COL_BDATE].date().month == (datetime.now() + timedelta(hours = 8)).date().month:
                output.append("%s | %s | %s\n " % (
                    get_fuzzily_discord_handle(row[MEMBER_INFO_COL_DISCORD], _df_discord_members), 
                    datetime.strftime(row[MEMBER_INFO_COL_BDATE], "%m-%d"),
                    get_num_days_away(row[MEMBER_INFO_COL_BDATE].date())
                    )
                )

        except Exception as e:
            continue

    await ctx.send(
        "```" + "".join(output) + "```"
    )

@bot.command(
    name='ink_resetday', 
    help='Resets day and repeats announcement'
)
async def reset_day(ctx):
    async with stuff_lock:
        cfg.curr_day = -1
        await ctx.send(
            "```Day reset!```" 
        )

@bot.command(
    name='ink_getscores', 
    help='Get Drawtober scores'
)
async def ink_get_scores_(ctx):
    print("here")
    await ink.get_scores(True)
    
@bot.command(
    name='waf_getscores', 
    help='Get Drawtober scores'
)
async def waf_get_scores_(ctx):
    print("here")
    await waf.get_scores(True)


@bot.command(
    name='bd_forgetshoutouts', 
    help='Forget who the bot has wished birthdays for.'
)
async def reset_shoutout_counter(ctx):
    _df = set_up_member_info()

    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if "bot-spam" in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    _df[MEMBER_INFO_BIRTHDAY_STATE] = [STATE_NO_SHOUTOUTS for i in range(_df.shape[0])]
    await channel.send(
        "```The Bot has forgotten when shoutouts were made!```"
    )
    update_birthday_state_to_gsheets(_df)

@bot.command(
    name='export', 
    help='Provide \"export DD MM DD MM YYYY\", with start date first and end date last. The year is optional, so no entry means current year.'
    )
async def export(ctx, channel: str, dd_begin: int, mm_begin: int, dd_end: int, mm_end: int, year=None):
    global df

    print(",", year, ",")

    if year is None:
        year = datetime.today().year

    df = set_up_palette_particulars_csv()
    await ctx.send(
        "```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
    )
    try:
        await get_photos(channel, dd_begin, mm_begin, dd_end, mm_end, year, ctx)
    except Exception as e:
        await ctx.send(
            "```Error occured! Contact the administrator. Message: %s```" % (str(e))
        )

@bot.command(
    name='ink_addmsgtoapprove', 
    help='If there are some approve messages that does not react to reactions, we use this command to add them back manually into the approve list.'
    )
async def add_msg_to_approve(ctx, link: str):
    global approve_queue

    # try:
    
    await get_msg_by_jump_url(bot, ctx, INKTOBER_APPROVE_CHANNEL, link.strip())   
    msg_to_approve = call_stack.pop() 
    msg_id = msg_to_approve.id
    if msg_id in approve_queue.keys():
        await ctx.send(
            "```Message is already in queue...```"
        )
        return

    link_to_msg_artwork = msg_to_approve.content.strip().split(" ")[-1]
    
    await get_msg_by_jump_url(bot, ctx, INKTOBER_RECEIVE_CHANNEL, link_to_msg_artwork)
    msg_artwork = call_stack.pop() 
    day = get_day(msg_artwork)

    approve_queue[msg_id] = (int(day), msg_artwork)
    await ctx.send(
        "```Added %d! Approve Queue contents is now: %s```" % (msg_id, ",".join([str(i) for i in approve_queue.keys()]))
    )
    # except Exception as e:
    #     await ctx.send(
    #         "```Error occured! Contact the administrator. Message: %s```" % (str(e))
    #     )


@bot.command(
    name='getallmembers', 
    help='Provide \"getallmembers VOICECHANNEL\", Outputs a list of members in a specified voice chat.'
    )
async def get_all_members(ctx, channel: str):
    global df
    df = set_up_palette_particulars_csv()
    await ctx.send(
        "```Aye aye capt'n! Checking for channel: %s. Please wait...```" % (channel)
    )
    try:
        await _get_all_members(channel, ctx)
    except Exception as e:
        await ctx.send(
            "```Error occured! Contact the administrator. Message: %s```" % (str(e))
        )

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    # Getting all the guilds our bot is in
    for guild in bot.guilds:
        # Adding each guild's invites to our dict
        invite_links[guild.id] = await guild.invites()
        print("--begin ", invite_links[guild.id])

    print(guild.roles)
        
    print(f'{bot.user} has connected to Discord!')
    if IS_HEROKU:
        bot.loop.create_task(birthday_task())
    if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
        bot.loop.create_task(ink.inktober_task())
    elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
        bot.loop.create_task(waf.waifuwars_task())

@bot.event
async def on_message(message):
    if message.channel.name == "bot-spam":
        await bot.process_commands(message)
        return 
    if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
        await ink.on_message_inktober(message, approve_queue)
    elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
        await waf.on_message_waifuwars(message, approve_queue)

@bot.event
async def on_raw_reaction_add(payload):
    if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
        await ink.on_raw_reaction_add_inktober(payload, approve_queue)
    elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
        await waf.on_raw_reaction_add_waifuwars(payload, approve_queue)



"""
    This code is referenced from https://medium.com/@tonite/finding-the-invite-code-a-user-used-to-join-your-discord-server-using-discord-py-5e3734b8f21f

    Applied for Extravaganza 2022; allow participants to join the Discord Server to attend lessons.
    The special invite code is https://discord.gg/ddekPqAckv.
"""
    

@bot.event
async def on_member_remove(member):
    
    # Updates the cache when a user leaves to make sure
    # everything is up to date
    
    invite_links[member.guild.id] = await member.guild.invites()

@bot.event
async def on_member_join(member):
    global EXTRAVAGANZA_INVITE_LINK 
    # Getting the invites before the user joining
    # from our cache for this specific guild

    invites_before_join = invite_links[member.guild.id]
    print("--before ", invite_links[member.guild.id])
    # Getting the invites after the user joining
    # so we can compare it with the first one, and
    # see which invite uses number increased

    invites_after_join = await member.guild.invites()
    print("--after ", invite_links[member.guild.id])

    # Loops for each invite we have for the guild
    # the user joined.

    for invite in invites_before_join:

        # Now, we're using the function we created just
        # before to check which invite count is bigger
        # than it was before the user joined.
        print(invite.uses)

        print(find_invite_by_code(invites_after_join, invite.code).uses)
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            
            # Now that we found which link was used,
            # we will print a couple things in our console:
            # the name, invite code used the the person
            # who created the invite code, or the inviter.
            
            print(f"Member {member.name} Joined")
            print(f"Invite Code: {invite.code}")
            print(f"Inviter: {invite.inviter}")
            
            # We will now update our cache so it's ready
            # for the next user that joins the guild

            invite_links[member.guild.id] = invites_after_join
            
            # We return here since we already found which 
            # one was used and there is no point in
            # looping when we already got what we wanted
            
            print(EXTRAVAGANZA_INVITE_LINK)
            if invite.code == EXTRAVAGANZA_INVITE_LINK:
                role = get(member.guild.roles, name=EXTRAVAGANZA_ROLE)
                await member.add_roles(role)
            else:
                role = get(member.guild.roles, name=MEMBER_ROLE)
                await member.add_roles(role)
            return

@bot.command(
    name='ex2022_kick_participants', 
    help='Kick all participants with the role: Extravaganza 2022 Participant'
)
async def ex2020_kick_participants(ctx):
    guild = get_guild(bot, GUILD)
    for member in guild.members:
        if member.roles[1].name == EXTRAVAGANZA_ROLE:
            await guild.kick(member, reason = "Thank you for joining Extravaganza 2022! Hope it has been fun for you :)") 

@bot.command(
    name='ex2022_set_new_invite', 
    help='Set a new invite link. If no link is provided, a new one is generated.'
)
async def ex2020_set_new_invite(ctx, updated_invite = None):
    global EXTRAVAGANZA_INVITE_LINK 
    guild = get_guild(bot, GUILD)
    link = None
    invites = await guild.invites()

    

    if updated_invite is None:
        link = await get_channel(bot, GUILD, "general").create_invite()
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
        
        if EXTRAVAGANZA_INVITE_LINK is not None:

            tmp = find_invite_by_code(invites, EXTRAVAGANZA_INVITE_LINK)
            if tmp is not None:
                await tmp.delete()

        EXTRAVAGANZA_INVITE_LINK = link
        print(EXTRAVAGANZA_INVITE_LINK, " is created")

    else:
        await ctx.send(
                    "```We cannot find the link. It is invalid.```"
                )    
    
    invite_links[guild.id] = await guild.invites()



def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv


if __name__ == "__main__":
    bot.run(TOKEN)


