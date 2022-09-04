import config_loader as cfg
import os
from models.DiscordBot import DiscordBot

from events.commons import register_events as register_events_commons
from events.birthdayTracker import register_events as register_events_birthday
from events.inktober import register_events as register_events_inktober
from events.member import register_events as register_events_member
from events.messages import register_events as register_events_messages
from events.waifuwars import register_events as register_events_waifuwars
from events.weeklyprompts import register_events as register_events_weeklyprompts

"""
    Command Handlers    
"""

if __name__ == "__main__":
  # Load environment
  cfg.load_env_by_command_line_args()
  register_events_commons()
  #register_events_member()
  register_events_birthday()
  register_events_inktober()
  register_events_messages()
  register_events_waifuwars()
  register_events_weeklyprompts()

  DiscordBot().run()


