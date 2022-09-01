"""
Handles Excel Sheet logic.
If you are not me, you should not temper with this.

https://docs.gspread.org/en/latest/
"""

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

import re, urllib
from urllib.request import urlopen, Request
import os
import numpy as np
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from requests.api import get
from difflib import SequenceMatcher

from utils.utils import get_file_path
PATH_MEMBER_INFO = "C:\\Users\\Looi Kai Wen\\OneDrive - National University of Singapore\\Post Welcome Tea Signups.xlsx"


spreadsheet = None

# Note: You can go to the sheets link via the following link:
# https://docs.google.com/spreadsheets/d/{{DOCID}}

from utils.commons import (
    DEFAULT_INKTOBER_STATE_DATA,
    DEFAULT_MESSAGES_DATA,
    DEFAULT_WEEKLYPROMPT_STATE_DATA,
    DF_COL,
    DF_ROW,
    DOCID_INKTOBER_TRACKER,
    DOCID_PALETTE_PARTICULARS_SURVEY,
    DOCID_WEEKLYPROMPTS_TRACKER,
    DOCID_BIRTHDAY_TRACKER,
    GSHEET_BIRTHDAY_COLUMNS,
    GSHEET_COLUMN_BIRTHDAY,
    GSHEET_COLUMN_DISCORD_ID,
    GSHEET_COLUMN_DISCORD,
    GSHEET_COLUMN_NAME,
    GSHEET_COLUMNS_MESSAGE_STATES,
    GSHEET_INKTOBER_COLUMNS,
    GSHEET_INKTOBER_COLUMN_STATE,
    GSHEET_INKTOBER_COLUMNS_MESSAGE_STATES,
    GSHEET_PLAYER_COLUMNS,
    GSHEET_WEEKLYPROMPT_COLUMN_STATE,
    GSHEET_WEEKLYPROMPT_COLUMNS,
    GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES,
    NUM_DAYS,
    NUM_WEEKS
)

PATH_TO_CREDENTIALS = "./cred/gsheets/credentials_excel.json"

qn_to_colnames = {
    "Birthday (DDMMYYYY)" : "Birthday",
    "Timestamp" : "Timestamp",
    "Disclaimer: I am willing to have my artwork posted in #session and #art-gallery, to be put up in NUS Palette Instagram.  " : "ArtPostOk",
    "Please fill in your full name!" : "Name",
    "Please fill in your telegram handle!" : "Telegram",
    "Please fill in your discord handle!" : "Discord", 
    "Please fill in links to your artworks, be it your Twitter handle, Instagram handle or Deviantart!" : "SNS",
    "Please fill in links to your artworks, be it your Twitter handle, Instagram handle or Deviantart![INSTA]" : "SNS_INSTA",
    "Please fill in links to your artworks, be it your Twitter handle, Instagram handle or Deviantart![TWITTER]" : "SNS_TWITTER",
    "Please fill in links to your artworks, be it your Twitter handle, Instagram handle or Deviantart![OTHERS]" : "SNS_OTHERS",
    "Please state your year of study! If you have graduated, just put \"Graduated\"" : "YStudy",
    "Please state your course of study!" : "Course",
    "Please share your length of experience with Palette, in number of semesters!" : "ExpPalette",
    "Please state your confidence in illustration skills!" : "IllustSkills",
    "Do you have the means to illustrate digitally? I.E You own a drawing tablet." : "Tablet",
    "Who are some of your favorite artists/manga?" : "FavArtist",
    "Tell us something fun about yourself! " : "Fun Stuff"
}

colnames_to_qn = {v: k for k, v in qn_to_colnames.items()}


csv_data = None

def get_member_info_from_gsheets():
    """ Used to handle automated birthday celebrations.
    """
    sheet = get_sheet_df_from_drive(os.getenv(DOCID_BIRTHDAY_TRACKER))
    #sheet = sheet.reset_index(drop=True)

    # birthdate_df[GSHEET_COLUMN_BIRTHDAY].transform(lambda x: x[1:] if not str(x)[0].isnumeric() else x)
    sheet[GSHEET_COLUMN_BIRTHDAY] = sheet[GSHEET_COLUMN_BIRTHDAY].transform(lambda x: '0'+ x if len(x) < 8 else x)
    # print(birthdate_df)
    sheet[GSHEET_COLUMN_BIRTHDAY] = pd \
        .to_datetime(sheet[GSHEET_COLUMN_BIRTHDAY], format='%m/%d/%Y', errors='coerce') \
        .fillna(pd.to_datetime(sheet[GSHEET_COLUMN_BIRTHDAY], format="%d%m%Y", errors="coerce"))

    return sheet.reset_index(drop=True)

def get_player_from_gsheets():
    """ Used to handle Inktober state persistence.
    """
    sheet = get_sheet_df_from_drive(
        os.getenv(DOCID_INKTOBER_TRACKER),
        name_dict=None,
        column_names=GSHEET_PLAYER_COLUMNS
    )

    sheet[GSHEET_WEEKLYPROMPT_COLUMN_STATE] = sheet[GSHEET_WEEKLYPROMPT_COLUMN_STATE] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna(("0;" * NUM_WEEKS)[:-1])

    # Clean data
    sheet[GSHEET_INKTOBER_COLUMN_STATE] = sheet[GSHEET_INKTOBER_COLUMN_STATE] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna(DEFAULT_INKTOBER_STATE_DATA)

    for column in GSHEET_COLUMNS_MESSAGE_STATES:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna(DEFAULT_MESSAGES_DATA)

    for column in GSHEET_PLAYER_COLUMNS:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna('')

    return sheet.reset_index(drop=True)

def get_inktober_from_gsheets():
    """ Used to handle Inktober state persistence.
    """
    sheet = get_sheet_df_from_drive(
        os.getenv(DOCID_INKTOBER_TRACKER),
        name_dict=None,
        column_names=GSHEET_INKTOBER_COLUMNS
    )

    # Clean data
    sheet[GSHEET_INKTOBER_COLUMN_STATE] = sheet[GSHEET_INKTOBER_COLUMN_STATE] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna(("0;" * NUM_DAYS)[:-1])

    output = sheet
    return output.reset_index(drop=True)

def get_weeklyprompts_from_gsheets():
    """ 
    Used to handle Weekly prompts state persistence.
    """
    sheet = get_sheet_df_from_drive(
        os.getenv(DOCID_WEEKLYPROMPTS_TRACKER), 
        name_dict=None, 
        column_names=GSHEET_WEEKLYPROMPT_COLUMNS
    )

    # Clean data
    for column in [GSHEET_WEEKLYPROMPT_COLUMN_STATE]:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna(DEFAULT_WEEKLYPROMPT_STATE_DATA)

    for column in GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna(DEFAULT_MESSAGES_DATA)

    return sheet.reset_index(drop=True)

"""
Unspool the Dataframe and populate along the numerous worksheets in the specified spreadsheet.
"""
def update_columns_to_gsheets(input_df, doc_id, column_names, name_dict=None):
    worksheets = get_spreadsheet_from_drive(doc_id).worksheets()
    # print(worksheets)
    # print(worksheets[0].title)
    offset = 0
    output_df = {}
    df_list = []
    #print(input_df)

    # Rearrange to have name, discord... columns on the leftmost
    column_names = [GSHEET_COLUMN_NAME, GSHEET_COLUMN_DISCORD, GSHEET_COLUMN_BIRTHDAY] + \
        list(filter(lambda x: x not in [GSHEET_COLUMN_NAME, GSHEET_COLUMN_DISCORD, GSHEET_COLUMN_BIRTHDAY], column_names))
    for id, worksheet in enumerate(worksheets, start = 1):
        print("Updating worksheet: ", worksheet.title)

        input_df = correct_df_header(input_df, name_dict = name_dict)

        #print(input_df.iloc[offset:])

        # Last worksheet is for lost souls
        if id == len(worksheets):
            output_df = input_df[column_names].iloc[offset:]
            # Remove unrecorded members under lost souls worksheet which exists in preceding worksheets.
            # https://towardsdatascience.com/8-ways-to-filter-pandas-dataframes-d34ba585c1b8
            if GSHEET_COLUMN_DISCORD_ID not in output_df.columns:
                continue
            temp_df = input_df.iloc[0 : offset]
            print(output_df)
            print(temp_df)
            # print(output_df.columns)
            # print(temp_df.columns)
            # print(input_df.iloc[offset : ][GSHEET_COLUMN_DISCORD_ID])
            # print(temp_df[GSHEET_COLUMN_DISCORD_ID])
            # print(output_df[
                # ~output_df.iloc[offset : ][GSHEET_COLUMN_DISCORD_ID].isin(
                    # temp_df[GSHEET_COLUMN_DISCORD_ID].values.tolist()
                # )
            # ].columns)
            output_df = output_df[
                ~output_df[GSHEET_COLUMN_DISCORD_ID].isin(
                    temp_df[GSHEET_COLUMN_DISCORD_ID].values.tolist()
                )
            ]

            print(output_df)

        else:
            output_df = pd.DataFrame(worksheet.get_all_values())
            if (output_df.empty):
                continue
            # Set column to first row, which is the header row in gsheet
            output_df.columns = output_df.iloc[0]
            # Remove the header row since it is not data.
            output_df = output_df.iloc[1:,:]
            output_df.reset_index(drop=True)

            len_worksheet = output_df.shape[DF_ROW]

            output_df = input_df[column_names].iloc[offset : offset + len_worksheet]

            offset += len_worksheet
        print(input_df)
        print(output_df)
        values = output_df.values.tolist()
        #print(values)
        #print([output_df.columns.values.tolist()] + values)
        worksheet.update([output_df.columns.values.tolist()] + values)
    print("Done upload!")
 
"""
Unspool the Dataframe and populate along the numerous worksheets in the specified spreadsheet.
"""
def update_birthday_state_to_gsheets(df):
    update_columns_to_gsheets(
        input_df=df,
        doc_id = os.getenv(DOCID_BIRTHDAY_TRACKER),
        column_names = GSHEET_BIRTHDAY_COLUMNS
    )

def update_inktober_state_to_gsheets(df):
    update_columns_to_gsheets(
        input_df=df,
        doc_id = os.getenv(DOCID_INKTOBER_TRACKER),
        column_names = GSHEET_INKTOBER_COLUMNS
    )

def update_weeklyprompt_state_to_gsheets(df):
    update_columns_to_gsheets(
        input_df=df,
        doc_id = os.getenv(DOCID_WEEKLYPROMPTS_TRACKER),
        column_names = GSHEET_WEEKLYPROMPT_COLUMNS
    )

def get_spreadsheet_from_drive(docid):
    global spreadsheet
    if spreadsheet is None:
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            get_file_path("cred", "gsheets"), 
            scope
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(docid)

    return spreadsheet

"""
Replace headers with the respective mapping.
"""
def correct_df_header(df, name_dict = qn_to_colnames):
    if name_dict is not None:
        df = df.rename(columns=name_dict)
    return df

"""
Get a Dataframe of all spreadsheets in the worksheet, concatanated one against the next.
"""
def get_sheet_df_from_drive(docid, name_dict = qn_to_colnames, column_names = None):
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(PATH_TO_CREDENTIALS, scope)
    df_list = []
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(docid)
    missing_column_names = None
    output_df = None
    worksheets = spreadsheet.worksheets()

    # Combine all sheets to one single dataframe.
    for id, worksheet in enumerate(worksheets, start = 1):

        worksheet_values = worksheet.get_all_values()

        if column_names is not None:
            try:
                exist_column_names = worksheet_values[0]
            except:
                continue
            missing_column_names = set(column_names) - set(exist_column_names)

        df_worksheet = pd.DataFrame(worksheet_values)


        # Set column to first row, which is the header row in gsheet
        df_worksheet.columns = df_worksheet.iloc[0]
        # Remove the header row since it is not data.
        df_worksheet = df_worksheet.iloc[1:,:]
        df_worksheet = correct_df_header(df_worksheet, name_dict)



        df_list.append(df_worksheet) 

    output_df = pd.concat(df_list)

    # It is assumed that all worksheets have the same columns.
    if column_names is not None and missing_column_names is not None:
        output_df = output_df.assign(
            **{k: np.nan for k in missing_column_names}
        )
    print(output_df)
    print("323")
    return output_df

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def get_name_from_discord_handle(discord_name):
    return discord_name.split('#')[0].strip()

def get_num_from_discord_handle(discord_name):
    return discord_name.split('#')[1].strip()

def similar_in_name(a, b):
    return similar(
        get_name_from_discord_handle(a).lower(), 
        get_name_from_discord_handle(b).lower(), 
    )

def similar_in_num(a, b):
    return similar(
        get_num_from_discord_handle("a" + a), 
        get_num_from_discord_handle("b" + b), 
    )

def verify_is_okay_to_share_by_discord_name(discord_name, df):
    discord_name_from_df = get_fuzzily_discord_handle(discord_name, df)
    _df = df.loc[df["Discord"] == discord_name_from_df]
    print(_df, _df["ArtPostOk"])
    return True if _df["ArtPostOk"].values[0] == "I agree" else False

def get_fuzzily_discord_handle(discord_name, member_df, get_uid = False):
    """
    Handles parsing of user-input Discord names and returns the name part
    """

    success_flag = False
    for index, row in member_df.iterrows():
        # if index == 0:
        #     continue
        try:
            if re.match(r'.+\#[0-9]{4}', discord_name):
                if similar_in_num(row["Discord"], discord_name) == 1 or similar_in_name(row["Discord"], discord_name) > 0.7:
                    success_flag = True
                    break
            else:
                if similar_in_name(row["Discord"], discord_name) > 0.7:
                    success_flag = True
                    break
        except Exception as err:
            print(err)
            pass
    if not success_flag: 
        return None

    return row["Discord"] if get_uid is False else str(row["uid"])

def get_social_handle_from_discord_name(df, discord_name, with_url = False):
    discord_name_from_df = get_fuzzily_discord_handle(discord_name, df)

    _df = df.loc[df['Discord'] == discord_name_from_df]
    print(_df)
    if _df["SNS_INSTA"].values[0].strip() != "":
        return [_df["SNS_INSTA"].values[0], "Instagram"]
    elif _df["SNS_TWITTER"].values[0].strip() != "":
        return [_df["SNS_TWITTER"].values[0], "Twitter"]
    elif _df["SNS_OTHERS"].values[0].strip() != "":
        if with_url:
            return [get_name_from_discord_handle(discord_name_from_df) + " (" + _df["SNS_OTHERS"].values[0] + ")", "Others"]
        else: 
            return [get_name_from_discord_handle(discord_name_from_df), "Others"]
    else:
        return [get_name_from_discord_handle(discord_name_from_df), "N.A"]

def pretty_print_social_handle_wrapper(name, df = None):
    if df is None:
        df = set_up_palette_particulars_csv()
    handle = get_social_handle_from_discord_name(df, name)
    if handle:
        return pretty_print_social_handle(handle)
    else:
        print(name, "failed to generate")

def pretty_print_social_handle(handle_type_pair):
    return "[%s] %s" % (
        handle_type_pair[1], handle_type_pair[0]
    )

def set_up_member_info():
    df = get_member_info_from_gsheets()
    return df

def set_up_inktober():
    df = get_inktober_from_gsheets()
    return df

def set_up_waifuwars():
    df = get_inktober_from_gsheets()
    return df

def set_up_weeklyprompts():
    df = get_inktober_from_gsheets()
    return df

def set_up_palette_particulars_csv():
    df = get_sheet_df_from_drive(os.getenv(DOCID_PALETTE_PARTICULARS_SURVEY))
    return df
