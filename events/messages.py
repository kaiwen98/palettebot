"""
Consolidates all commands that is related to the birthdayTracker.
"""
from controller.DiscordBot import DiscordBot
from controller import inktober as ink
import asyncio
from controller.birthdayTracker import birthday_task
from controller import waifuwars as waf
from controller.excelHandler import (
    MEMBER_INFO_BIRTHDAY_STATE,
    MEMBER_INFO_COL_BDATE,
    MEMBER_INFO_COL_DISCORD,
    STATE_NO_SHOUTOUTS,
    get_fuzzily_discord_handle,
    set_up_member_info,
    update_birthday_state_to_gsheets
)

import datetime
import os
import pandas as pd

import config_loader as cfg
from controller.DiscordBot import DiscordBot
from utils.commons import ART_FIGHT_MODE_INKTOBER, ART_FIGHT_MODE_WAIFUWARS, ART_FIGHT_STATE


def register_events():
    bot = DiscordBot().bot
    @bot.event
    async def on_message(message):
        print(message)
        if os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_INKTOBER:
            await ink.on_message(message, DiscordBot().approve_queue)
        elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WAIFUWARS:
            await waf.on_message_waifuwars(message, DiscordBot().approve_queue)
        elif message.channel.name == "bot-spam":
            await bot.process_commands(message)
            return 

    @bot.event
    async def on_raw_reaction_add(payload):
        if ART_FIGHT_STATE == ART_FIGHT_MODE_INKTOBER:
            await ink.on_raw_reaction_add(payload, DiscordBot().approve_queue)
        elif ART_FIGHT_STATE == ART_FIGHT_MODE_WAIFUWARS:
            await waf.on_raw_reaction_add(payload, DiscordBot().approve_queue)

