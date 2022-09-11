from config_loader import (
  get_recorded_date,
  get_recorded_datetime,
  get_recorded_week,
  set_recorded_date,
  set_recorded_datetime,
  set_recorded_week
)
from utils.utils import get_today_datetime, get_week_from_datetime


def is_done_this_day(hour=None):
  if get_recorded_date() == None:
    set_recorded_date(get_today_datetime().date())
    return True

  if (
    # This week
    get_recorded_date() != \
      get_today_datetime().date() 
    # At this hour
      and (hour is None or get_today_datetime() == hour) 
  ):
    set_recorded_date(get_today_datetime().date())
    return False
  return True

def is_done_this_week(hour=None):
  if get_recorded_week() == None:
    set_recorded_week(get_week_from_datetime(get_today_datetime()))

  if (
    # This week
    get_recorded_week() != \
      get_week_from_datetime(get_today_datetime()) 
    # At this hour
      and (hour is None or get_today_datetime() == hour) 
  ):
    set_recorded_week(get_week_from_datetime(get_today_datetime()))
    return False

  print(
    "Week: ", 
    get_week_from_datetime(get_today_datetime())
  )

  print(
    "Hour: ", 
    get_today_datetime().hour
  )
  return True
