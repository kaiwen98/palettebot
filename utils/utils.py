from datetime import datetime
from datetime import timedelta
import os

from utils.commons import (
  DIR_OUTPUT, 
  DISCORD_CHANNEL_WAIFU_WARS,
  DISCORD_GUILD, 
  DISCORD_MESSAGES_LIMIT,
  ENV
)


def get_file_path(*path):
  path = os.path.join(os.getcwd(), *path)
  if not os.path.isdir(path):
      return path
  file_name = list(os.listdir(path))[0]
  return os.path.join(path, file_name)

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

def get_week_from_curr_datetime(input_datetime):
  sem1_week_offset = datetime(datetime.today().year, 8, 9)
  sem2_week_offset = datetime(datetime.today().year, 1, 9)
  return input_datetime.isocalendar()[1] + 1 - \
    sem1_week_offset.isocalendar()[1] \
    if input_datetime > sem1_week_offset \
    else sem2_week_offset.isocalendar()[1]

def get_today_date():
  # Gets date with time zone accounted for/=
  # SGT = UTC + 8hrs
  date = datetime.now() + (
    timedelta(
      hours = 8 if os.getenv(ENV) == 'production' else 0
    )   
  )
  return date.date()

def get_num_days_away(member_date):
  dummy_member_date = datetime(
    day=member_date.day,
    month=member_date.month,
    year=2000
  )

  # +8 hours to account for time zone difference in Heroku
  dummy_curr_date = datetime.now() + (
    timedelta(
      hours = 8 if os.getenv(ENV) == 'production' else 0
    )   
  )

  dummy_curr_date = datetime(
    day=dummy_curr_date.date().day,
    month=dummy_curr_date.date().month,
    year=2000
  )

  days_away = dummy_curr_date - dummy_member_date 
  # print(
  #     "current time: ", dummy_curr_date,
  #     "bday: ", dummy_member_date
  # )
  # print(days_away.days)

  num_days_away = -1 * days_away.days

  if num_days_away < 0: 
    num_days_away = 365 + num_days_away
  return num_days_away


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

def get_day_from_message(message):
  if len(message.content.strip().split(" ")) == 2:
    return int(message.content.strip().split(" ")[1])
  else:
    return get_today_date().day









