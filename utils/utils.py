from datetime import datetime
from datetime import timedelta
import os

from config_loader import GUILD, IS_HEROKU, call_stack, call_stack_waifuwars, bot
from utils.commons import DIR_OUTPUT, DISCORD_CHANNEL_WAIFU_WARS, DISCORD_MESSAGES_LIMIT
def get_zip_file_size(zp):
    size = sum([zinfo.file_size for zinfo in zp.filelist])
    return float(size) / 1000  # kB

def clear_folder(folder = "io"):
    import os, shutil
    for filename in os.listdir(os.path.join(os.getcwd(), folder)):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def get_timestamp_from_curr_datetime():
    output = datetime.now().strftime("%m%d%Y_%H%M%S")
    return output.strip()

def get_today_date(is_heroku = False):
    date = datetime.now() + timedelta(hours = 8) if is_heroku else datetime.now()
    return date.date().day

def get_num_days_away(member_date):
    dummy_member_date = datetime(
        day=member_date.day,
        month=member_date.month,
        year=2000
    )

    dummy_curr_date = datetime.now() + timedelta(hours = 8)
    dummy_curr_date = datetime(
        day=dummy_curr_date.date().day,
        month=dummy_curr_date.date().month,
        year=2000
    )


    days_away = dummy_curr_date - dummy_member_date 
    # +8 hours to account for time zone difference in Heroku
    # print(
    #     "current time: ", dummy_curr_date,
    #     "bday: ", dummy_member_date
    # )
    # print(days_away.days)

    num_days_away = -1 * days_away.days

    if num_days_away < 0: 
        num_days_away = 365 + num_days_away
    return num_days_away

def get_channel(bot, GUILD, channel_name):
    for guild in bot.guilds:
        if guild.name == GUILD:
            break
    for g_channel in guild.channels:
        if channel_name in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            return channel
    
    return False

async def remove_messages(messages_to_delete):
    for message in messages_to_delete:
        await message.delete()
    messages_to_delete.clear()

def calculate_score(state):
    return list(state).count("2")

def get_rank_emoji(rank):
    if rank == 1:
        return ":first_place:"
    if rank == 2:
        return ":second_place:"
    if rank == 3:
        return ":third_place:"
    else:
        return ":paintbrush:"

def get_day(message):
    if len(message.content.strip().split(" ")) == 2:
        return int(message.content.strip().split(" ")[1])
    else:
        return get_today_date(IS_HEROKU)

async def get_attacked_user(message):
    output = []
    if len(message.content.strip().split(" ")) >= 2:
        tags = message.content.strip().split(" ", 1)[1]
        print(tags)
        messages = await get_channel(bot, GUILD, DISCORD_CHANNEL_WAIFU_WARS).history(
            limit = DISCORD_MESSAGES_LIMIT,
            ).flatten()
        for tag in tags.strip().split(" "):
            id = get_id_from_tag(tag)
            tmp = await get_waifu_of_user(id, messages)
            output.append(tmp)
        print(output)
    return output

async def get_waifu_of_user(id, messages = None):
    print(id)
    if messages is None:
        messages = await get_channel(bot, GUILD, DISCORD_CHANNEL_WAIFU_WARS).history(
            limit = DISCORD_MESSAGES_LIMIT,
            ).flatten()
    for message in messages: 
        # print(id, message.author.id, message.content)
        if message.author.id == int(id.strip()) and len(message.attachments) > 0:
            return message


def get_id_from_tag(tag):
    return tag[3:-1]


async def get_msg_by_jump_url(bot, ctx, channel, jump_url):

    for guild in bot.guilds:
        print(guild)
        if guild.name == GUILD:
            break

    for g_channel in guild.channels:
        if channel in g_channel.name:
            channel = guild.get_channel(g_channel.id)
            break

    if channel is None: 
        await ctx.send(
            "Channel not recognised. Make sure you spelt it right!"
        )
        return None

    messages = await channel.history(
        limit = DISCORD_MESSAGES_LIMIT,
        ).flatten()

    for message in messages: 
        print(message.jump_url, jump_url)
        if message.jump_url == jump_url:
            print("hahah")
            call_stack.append(message)
            return
    
    return None