"""
Consolidates all commands that is related to the birthdayTracker.
"""
from models.AsyncManager import AsyncManager
from models.DiscordBot import DiscordBot
from controller import inktober as ink
from controller import weeklyprompts as weekp
import asyncio
from controller import waifuwars as waf
from controller.excelHandler import (
    get_fuzzily_discord_handle,
    set_up_member_info,
    update_birthday_state_to_gsheets
)

import datetime
import os
import pandas as pd
from config_loader import (
    GLOBAL_WEEKLYPROMPT_ISON, 
)
from utils.constants import ART_FIGHT_MODE_INKTOBER, ART_FIGHT_MODE_WAIFUWARS, ART_FIGHT_MODE_WEEKLY_PROMPTS, ART_FIGHT_STATE


def register_events():
    bot = DiscordBot().bot
    @bot.event
    async def on_message(message):
        async with AsyncManager().lock:
            if os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_INKTOBER:
                await ink.on_message(message, DiscordBot().approve_queue)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WAIFUWARS:
                await waf.on_message_waifuwars(message, DiscordBot().approve_queue)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WEEKLY_PROMPTS:
                await weekp.on_message(message)
            elif message.channel.name == "bot-spam":
                await bot.process_commands(message)

    @bot.event
    async def on_message_edit(message_before, message_after):
        async with AsyncManager().lock:
            if os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_INKTOBER:
                await ink.on_message(message_after, DiscordBot().approve_queue)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WAIFUWARS:
                await waf.on_message_waifuwars(message_after, DiscordBot().approve_queue)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WEEKLY_PROMPTS:
                await weekp.on_message(message_after)
            elif message_before.channel.name == "bot-spam":
                await bot.process_commands(message_after)

    @bot.event
    async def on_raw_reaction_add(payload):
        async with AsyncManager().lock:
            print("pepe")
            print(os.getenv(GLOBAL_WEEKLYPROMPT_ISON))
            print(os.getenv(ART_FIGHT_STATE))
            if os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_INKTOBER:
                await ink.on_raw_reaction_add(payload, DiscordBot().approve_queue)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WEEKLY_PROMPTS:
                await weekp.on_raw_reaction_add(payload)
            elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WAIFUWARS:
                await waf.on_raw_reaction_add(payload, DiscordBot().approve_queue)

