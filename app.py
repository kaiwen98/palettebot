import os
from controller.excelHandler import set_up_gsheets
from controller.gdrive_uploader import set_up_gdrive
from models.DiscordBot import DiscordBot

from events.commons import register_events as register_events_commons
from events.birthdayTracker import register_events as register_events_birthday
from events.inktober import register_events as register_events_inktober
from events.member import register_events as register_events_member
from events.messages import register_events as register_events_messages
from events.waifuwars import register_events as register_events_waifuwars
from events.weeklyprompts import register_events as register_events_weeklyprompts
from config_loader import load_env_by_command_line_args
"""
    Command Handlers    
"""

if __name__ == "__main__":
  # Load environment
  load_env_by_command_line_args()
  set_up_gdrive()
  set_up_gsheets()
  register_events_commons()
  #register_events_member()
  register_events_birthday()
  register_events_inktober()
  register_events_messages()
  register_events_waifuwars()
  register_events_weeklyprompts()

  DiscordBot().run()


