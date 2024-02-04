import requests
import re
from config_loader import reset_config
from enum import IntEnum
from models.DiscordBot import DiscordBot
from utils.constants import (
    ART_FIGHT_MODE_NOTHING,
    ART_FIGHT_MODE_WEEKLY_PROMPTS,
    ART_FIGHT_STATE,
    DIR_OUTPUT,
    ID_PERIOD_PROMPT_LIST, 
    NUS_CALENDAR_PERIOD_TYP_LIST, 
    NUS_CALENDAR_PERIOD_TYP_SEM1A,
    NUS_CALENDAR_PERIOD_TYP_SEM1B,
    NUS_CALENDAR_PERIOD_TYP_SEM1R,
    NUS_CALENDAR_PERIOD_TYP_SEM1VA,
    NUS_CALENDAR_PERIOD_TYP_SEM1VB,
    NUS_CALENDAR_PERIOD_TYP_SEM2A,
    NUS_CALENDAR_PERIOD_TYP_SEM2B,
    NUS_CALENDAR_PERIOD_TYP_SEM2R,
    NUS_CALENDAR_PERIOD_TYP_SEM2V,
)
from controller.excelHandler import (
    get_spreadsheet,
    set_up_gsheets
)
import gspread
import os
from models.Singleton import Singleton
from utils.utils import get_today_datetime, get_today_week

"""
Default semester period values to use
If it cannot be retrieved from the configuration sheet.
"""
default_semester_period_value_matrix = [
    [NUS_CALENDAR_PERIOD_TYP_SEM1A, 
    (
      (8, 9), # week 1
      (9, 12) # week 6
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM2A, 
    (
      (1, 9),
      (2, 13)
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM1R,
    (
      (9, 17), # week 1
      (9, 25) # week 6
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM2R,
    (
      (2, 18),
      (2, 26)
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM1B,
    (
      (9, 26), # week 7 
      (11, 7) # week 13
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM2B,
    (
      (2, 27),
      (4, 10)
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM1VA,
    (
      (12, 4),
      (12, 31)
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM1VB,
    (
      (1, 1),
      (1, 8)
    )
    ],
    [NUS_CALENDAR_PERIOD_TYP_SEM2V,
    (
      (3, 7),
      (8, 6)
    )
    ]
  ]

class EWorkSheets(IntEnum):
    CONFIG = 0
    TELEMETRY = 1
    SEM1_PROMPTS = 2
    SEM1V_PROMPTS = 3
    SEM2_PROMPTS = 4
    SEM2V_PROMPTS = 5

class EBotState(IntEnum):
    STARTING = 0
    WEEKLYPROMPT = 1
    STOPPED = 2

class Prompt():
    def __init__(self, prompt, emoji):
        self.prompt = prompt
        self.emoji = emoji

class ConfigurationSheet(metaclass=Singleton):
    def setup(self, *args, **kw):
        print("[LOG] Called ConfigurationSheet init")
        self.worksheets: list[gspread.models.Worksheet]
        self.prompt_value_matrix: list = list(range(len(ID_PERIOD_PROMPT_LIST)))
        self.config_value_matrix: list
        self.telemetry_value_matrix: list
        self.semester_period = []
        self.prompts = {i: {} for i in ID_PERIOD_PROMPT_LIST}
        self.config = {}
        self.doc_id: str
        self.err_msg: str = "No Error"
        self.bot_state: EBotState
        self.bot_state = EBotState.STARTING
    
    def set_err_msg(self, msg: str):
        self.err_msg = msg

    def set_bot_state(self, state: EBotState):
        self.bot_state = state

    def refresh(self):
        # Retrieve spreadsheet
        self.get_spreadsheet()
        # Update env values
        self.process_config()
        # Update prompts
        self.process_prompt()
        # Update Commands
        self.process_cmds()
        # Update Telemetry
        self.process_telemetry()

    def get_spreadsheet(self):
        set_up_gsheets()
        self.doc_id = os.getenv("DOCID_CONFIGURATION")
        # print("[LOG] ", self.doc_id, os.getenv("DOCID_CONFIGURATION"))
        spreadsheet = get_spreadsheet(self.doc_id)
        self.worksheets = spreadsheet.worksheets()
        print(self.worksheets[0].get_values())
        
        self.config_value_matrix = self.worksheets[int(EWorkSheets.CONFIG)].get_values()

        self.telemetry_value_matrix = self.worksheets[int(EWorkSheets.TELEMETRY)].get_values()

        for i in ID_PERIOD_PROMPT_LIST:
            self.prompt_value_matrix[i] = self.worksheets[int(EWorkSheets.SEM1_PROMPTS + i)].get_values()
    
    def process_cmds(self):
        for i in range(len(self.telemetry_value_matrix)):
            key = self.telemetry_value_matrix[i][0]
            value = self.telemetry_value_matrix[i][1]

            # Handle response
            if key == 'CLEAR_WEEK_STATE':
                if value != 'WAITING FOR COMMANDS - 1':
                    print("[LOG] Config cleared!")
                    reset_config()
                    self.err_msg = "Cleared week state!"
                self.telemetry_value_matrix[i][1] = 'WAITING FOR COMMANDS - 1'
                     
            if key == 'CLEAR_ALL_SCORES':
                if value == os.getenv("PASSWORD"):
                    print("[LOG] Cleared Player scores!")
                    for player_key in DiscordBot().players.keys():
                        DiscordBot().players[player_key].reset_weeklyprompt_scores()

                    self.err_msg = "Cleared all scores!"
                self.telemetry_value_matrix[i][1] = 'WAITING FOR COMMANDS - Password'

    def process_telemetry(self):
        for i in range(len(self.telemetry_value_matrix)):
            key = self.telemetry_value_matrix[i][0]
            value = self.telemetry_value_matrix[i][1]

            period_name, curr_week = get_today_week()
             
            if key == 'BOT_PERIOD':
                self.telemetry_value_matrix[i][1] = period_name
            if key == 'BOT_WEEK':
                self.telemetry_value_matrix[i][1] = curr_week
            if key == 'BOT_LAST_ALIVE':
                bot_last_alive_count = int(self.telemetry_value_matrix[i][1])
                self.telemetry_value_matrix[i][1] = str(bot_last_alive_count + 1)
            if key == "BOT_DATETIME":
                self.telemetry_value_matrix[i][1] = str(get_today_datetime())
            if key == "BOT_MSG":
                self.telemetry_value_matrix[i][1] = self.err_msg
            if key == "BOT_STATE":
                msg: str
                if self.bot_state == EBotState.STARTING:
                    msg = "Starting up"
                elif self.bot_state == EBotState.STOPPED:
                    msg = "Bot Stopped"
                elif self.bot_state == EBotState.WEEKLYPROMPT:
                    msg = "Running WeeklyPrompts"
                self.telemetry_value_matrix[i][1] = msg
        self.worksheets[int(EWorkSheets.TELEMETRY)].update(self.telemetry_value_matrix)

    def process_config(self):
        self.config.clear()
        for i in range(len(self.config_value_matrix)):
            key = self.config_value_matrix[i][0]
            value = self.config_value_matrix[i][1]
            # Cannot set password here
            if key == 'PASSWORD':
                continue
            self.config[key] = value
            os.environ[key] = value

        if os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_NOTHING:
            self.bot_state = EBotState.STOPPED
        elif os.getenv(ART_FIGHT_STATE) == ART_FIGHT_MODE_WEEKLY_PROMPTS:
            self.bot_state = EBotState.WEEKLYPROMPT
        else:
            self.bot_state = EBotState.STOPPED

        self.process_semester_ranges()

    def process_semester_ranges(self):
        self.semester_period.clear()
        for period in NUS_CALENDAR_PERIOD_TYP_LIST:
            if (
                (period + "_START") in self.config.keys()
                and (period + "_END") in self.config.keys()
            ):
                start_date = self.config[period + "_START"].split('/')
                end_date = self.config[period + "_END"].split('/')
                self.semester_period.append(
                    [period, 
                    (   # Start Month   Start Year
                        (int(start_date[0]), int(start_date[1])),
                        # Start Month   Start Year
                        (int(end_date[0]),   int(end_date[1])),
                    )]
                )
            else:
                self.semester_period = default_semester_period_value_matrix
                break

    def process_prompt(self):
        for p in ID_PERIOD_PROMPT_LIST:
            self.prompts[p].clear()
            # Number of distinct weeks = Num of prompt sets
            num_prompt_sets = len(self.prompt_value_matrix[p][0])

            for i in range(num_prompt_sets):
                # Validation phase

                # Week number is numeric
                if not self.prompt_value_matrix[p][0][i].isnumeric():
                    continue

                # Dont have at least 4 rows
                if i > (len(self.prompt_value_matrix[p][3]) - 1):
                    continue
                
                week_no = int(self.prompt_value_matrix[p][0][i])
                self.prompts[p][week_no] = \
                    {
                        "week_number": self.prompt_value_matrix[p][0][i],
                        "prompts": [],
                        "screencap_img_gdrive_desc": self.prompt_value_matrix[p][-2][i],
                        "screencap_img_gdrive_url": self.prompt_value_matrix[p][-1][i]
                    }

                for prompt_list in self.prompt_value_matrix[p][1:-2]:
                    # if not '' or empty cell
                    if len(prompt_list[i]) <= 0:
                        continue

                    toks = prompt_list[i].split(';')
                    prompt = toks[0]
                    if len(toks) > 1:
                        emoji = toks[1]
                    else:
                        emoji = ''
                    self.prompts[p][week_no]["prompts"].append({
                        "prompt": prompt,
                        "emoji": emoji
                    })
        
    def getGidFromGdriveUrl(self, url):
        """Parse a Gdrive share link/upload link to retrieve the Gdrive Id.

        Args:
            url (string): Gdrive URL

        Returns:
            string: Gdrive Id
        """
        # To deal with a different gdrive url format
        url = url.replace(r'file/d/', "?id=")
        url = re.sub(r'(\/v.*)', "", url)
        return re.split(r'\?id\=', url)[1]
    
    def downloadImageByGid(self, gid:str):
        url = f"https://drive.google.com/u/0/uc?id={gid}&export=download"
        print(url)
        r = requests.get(url, stream=True)
        r.raw.decode_content = True
        print(r.headers['content-disposition'])
        fname = re.search(r'(?<=(filename=\")).*(?=\")', r.headers["Content-Disposition"]).group()
        print(fname)
        return fname, r.content
    
    def __init__(self):
        pass
