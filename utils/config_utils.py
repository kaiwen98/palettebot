from config_loader import (
  get_recorded_date,
  get_recorded_datetime,
  get_recorded_week,
  set_recorded_date,
  set_recorded_datetime,
  set_recorded_week
)
from utils.utils import get_today_datetime, get_week_from_datetime


def is_done_this_day():
  if (
      get_recorded_date() \
      and get_recorded_date() == \
        get_today_datetime().date()
  ):
    return True
  set_recorded_date(get_today_datetime().date())
  return False

def is_done_this_week(hour=None):
  if (
    get_recorded_week() \
    and hour is None or get_today_datetime().hour == hour \
    and get_recorded_week() == \
      get_week_from_datetime(get_today_datetime())
  ):
    print(
      "Week: ", 
      get_week_from_datetime(get_today_datetime())
    )

    print(
      "Hour: ", 
      get_today_datetime().hour
    )
    return True
  set_recorded_week(get_week_from_datetime(get_today_datetime()))
  return False
