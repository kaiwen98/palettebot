from config_loader import (
  get_recorded_date,
  get_recorded_datetime,
  get_recorded_week,
  set_recorded_date,
  set_recorded_datetime,
  set_recorded_week
)
from utils.utils import get_today_datetime, get_week_from_datetime


def is_done_this_day(hour=None, reset=None):
  if get_recorded_date() == None:
    set_recorded_date(get_today_datetime().date())
    if reset != None:
      return reset

  if (
    # This week
    (
      get_recorded_date() \
      != get_today_datetime().date() 
    )
    # At this hour
    and (
      hour is None 
      or get_today_datetime().hour == int(hour)
    ) 
  ):
    set_recorded_date(get_today_datetime().date())
    return False
  return True

def is_done_this_week(hour=None, reset=None):

  print(get_recorded_week())
  print(hour)
  period, week = get_week_from_datetime(get_today_datetime())

  if get_recorded_week() == None:
    set_recorded_week(period, week)
    if reset != None:
      return reset

  if (
    # This week
    (
      get_recorded_week() \
      != week
    ) 
    # At this hour
    and (
      hour is None 
      or get_today_datetime().hour == int(hour)
    ) 
  ):
    set_recorded_week(period, week)
    return False

  print(
    f"Week: {week} - {period}", 
  )

  print(
    "Hour: ", 
    get_today_datetime().hour
  )

  return True
