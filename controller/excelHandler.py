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

from utils.utils import get_file_path
PATH_MEMBER_INFO = "C:\\Users\\Looi Kai Wen\\OneDrive - National University of Singapore\\Post Welcome Tea Signups.xlsx"
MEMBER_INFO_COL_DISCORD = "Discord"
MEMBER_INFO_COL_BDATE = "Birthday (DDMMYYYY)"
MEMBER_INFO_BIRTHDAY_STATE = "BIRTHDAY_STATE"
MEMBER_INFO_NAME = "Name"

INKTOBER_STATE = "INKTOBER_STATE"
WAIFUWARS_NUMATTACKED = "WAIFUWARS_NUMATTACKED"
WAIFUWARS_NUMATTACKING = "WAIFUWARS_NUMATTACKING"
STATE_NO_SHOUTOUTS = 0b00
STATE_SHOUTOUT_WEEK = 0b10
STATE_SHOUTOUT_DAY = 0b01

STATE_DID_NOT_ATTEMPT = 0
STATE_UNDER_APPROVAL = 1
STATE_APPROVED = 2

# Note: You can go to the sheets link via the following link:
# https://docs.google.com/spreadsheets/d/{{DOCID}}

from utils.commons import (
    DOCID_INKTOBER_TRACKER,
    DOCID_PALETTE_PARTICULARS_SURVEY,
    DOCID_WEEKLYPROMPTS_TRACKER,
    DOCID_BIRTHDAY_TRACKER,
    GSHEET_WEEKLYPROMPT_STATE,
    GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES,
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


csv_data = None

def get_member_info_from_gsheets():
    """ Used to handle automated birthday celebrations.
    """
    sheet = get_sheet_df_from_drive(os.getenv(DOCID_BIRTHDAY_TRACKER))
    #sheet = sheet.reset_index(drop=True)

    # birthdate_df[MEMBER_INFO_COL_BDATE].transform(lambda x: x[1:] if not str(x)[0].isnumeric() else x)
    sheet[MEMBER_INFO_COL_BDATE] = sheet[MEMBER_INFO_COL_BDATE].transform(lambda x: '0'+ x if len(x) < 8 else x)
    # print(birthdate_df)
    sheet[MEMBER_INFO_COL_BDATE] = pd \
        .to_datetime(sheet[MEMBER_INFO_COL_BDATE], format='%m/%d/%Y', errors='coerce') \
        .fillna(pd.to_datetime(sheet[MEMBER_INFO_COL_BDATE], format="%d%m%Y", errors="coerce"))

    return sheet.reset_index(drop=True)

def get_inktober_from_gsheets():
    """ Used to handle Inktober state persistence.
    """
    sheet = get_sheet_df_from_drive(os.getenv(DOCID_INKTOBER_TRACKER))

    inktober_df = sheet

    # Clean data
    inktober_df[INKTOBER_STATE] = inktober_df[INKTOBER_STATE] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna("0" * 31)
    inktober_df[WAIFUWARS_NUMATTACKED] = inktober_df[WAIFUWARS_NUMATTACKED] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna("0")
    inktober_df[WAIFUWARS_NUMATTACKING] = inktober_df[WAIFUWARS_NUMATTACKING] \
        .replace(r'^\s*$', np.nan, regex=True) \
        .fillna("0")

    output = inktober_df
    return output.reset_index(drop=True)

def get_weeklyprompts_from_gsheets():
    """ 
    Used to handle Weekly prompts state persistence.
    """
    sheet = get_sheet_df_from_drive(os.getenv(DOCID_WEEKLYPROMPTS_TRACKER), column_names=[GSHEET_WEEKLYPROMPT_STATE, *GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES])


    # Clean data
    for column in [GSHEET_WEEKLYPROMPT_STATE]:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna("0" * NUM_WEEKS)

    for column in GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES:
        sheet[column] = sheet[column] \
            .replace(r'^\s*$', np.nan, regex=True) \
            .fillna('')

    return sheet.reset_index(drop=True)

# def update_birthday_state_to_gsheets(df):
# print(os.getenv(DOCID_BIRTHDAY_TRACKER))
# sheet = get_spreadsheet_from_drive(os.getenv(DOCID_BIRTHDAY_TRACKER)).worksheets()
# print(sheet)
# print(sheet[0].title)
# df_juniors = sheet[0]
# df_seniors = sheet[1]
# num_rows_df_seniors = len(df_juniors.get_all_values())-1
# # print(df[MEMBER_INFO_COL_BDATE])
# for i in [(df_juniors, "Juniors", [0, num_rows_df_seniors-1]), (df_seniors, "Seniors", [num_rows_df_seniors, df.shape[0]-1])]:
# # print(i[1])
# _df = pd.DataFrame(i[0].get_all_values())
# _df = correct_df_header(_df, name_dict = None)
# _df[MEMBER_INFO_BIRTHDAY_STATE] = df[MEMBER_INFO_BIRTHDAY_STATE].loc[i[2][0]:i[2][1]].values.tolist()
# values = _df.values.tolist()
# # print("haha")
# # print([_df.columns.values.tolist()] + values)
# i[0].update([_df.columns.values.tolist()] + values)

"""
Unspool the Dataframe and populate along the numerous worksheets in the specified spreadsheet.
"""
def update_birthday_state_to_gsheets(input_df):
    print(os.getenv(DOCID_BIRTHDAY_TRACKER))
    worksheets = get_spreadsheet_from_drive(os.getenv(DOCID_BIRTHDAY_TRACKER)).worksheets()
    print(worksheets)
    print(worksheets[0].title)
    offset = 0
    for worksheet in worksheets:
        print("Updating worksheet: ", worksheet.title)
        output_df = pd.DataFrame(worksheet.get_all_values())
        output_df = correct_df_header(output_df, name_dict = None)

        len_worksheet = len(worksheet.get_all_values())

        output_df[MEMBER_INFO_BIRTHDAY_STATE] = input_df[MEMBER_INFO_BIRTHDAY_STATE].loc[offset : offset + len_worksheet - 1].values.tolist()

        offset += len_worksheet

        values = output_df.values.tolist()

        worksheet.update([output_df.columns.values.tolist()] + values)

"""
Unspool the Dataframe and populate along the numerous worksheets in the specified spreadsheet.
"""
def update_inktober_state_to_gsheets(input_df):
    print(os.getenv(DOCID_BIRTHDAY_TRACKER))
    worksheets = get_spreadsheet_from_drive(os.getenv(DOCID_BIRTHDAY_TRACKER)).worksheets()
    print(worksheets)
    print(worksheets[0].title)
    offset = 0
    for worksheet in worksheets:
        print("Updating worksheet: ", worksheet.title)
        output_df = pd.DataFrame(worksheet.get_all_values())
        output_df = correct_df_header(output_df, name_dict = None)

        len_worksheet = len(worksheet.get_all_values())
        for column in [INKTOBER_STATE, WAIFUWARS_NUMATTACKING, WAIFUWARS_NUMATTACKED]:
            output_df[column] = input_df[MEMBER_INFO_BIRTHDAY_STATE].loc[offset : offset + len_worksheet - 1].values.tolist()

        offset += len_worksheet

        values = output_df.values.tolist()

        worksheet.update([output_df.columns.values.tolist()] + values)


def update_inktober_state_to_gsheets(df):
    sheet = get_spreadsheet_from_drive(os.getenv(DOCID_INKTOBER_TRACKER)).worksheets()
    df1 = sheet[0]
    df2 = sheet[1]
    sheet1_rows = len(df1.get_all_values())-1
    # print(df[MEMBER_INFO_COL_BDATE])
    print(df)
    for i in [(df1, "Juniors", [0, sheet1_rows-1]), (df2, "Seniors", [sheet1_rows, df.shape[0]-1])]:
        # print(i[1])
        _df = pd.DataFrame(i[0].get_all_values())
        _df = correct_df_header(_df, name_dict = None)
        for j in [INKTOBER_STATE, WAIFUWARS_NUMATTACKING, WAIFUWARS_NUMATTACKED]:
            print(j)
            _df[j] = df[j].loc[i[2][0]:i[2][1]].values.tolist()
        values = _df.values.tolist()
        # print("haha")
        # print([_df.columns.values.tolist()] + values)
        i[0].update([_df.columns.values.tolist()] + values)

def update_weeklyprompt_state_to_gsheets(df):
    sheet = get_spreadsheet_from_drive(os.getenv(DOCID_WEEKLYPROMPTS_TRACKER)).worksheets()
    df1 = sheet[0]
    df2 = sheet[1]
    sheet1_rows = len(df1.get_all_values())-1
    # print(df[MEMBER_INFO_COL_BDATE])
    print(df)
    for i in [(df1, "Juniors", [0, sheet1_rows-1]), (df2, "Seniors", [sheet1_rows, df.shape[0]-1])]:
        # print(i[1])
        _df = pd.DataFrame(i[0].get_all_values())
        _df = correct_df_header(_df, name_dict = None)
        for j in [INKTOBER_STATE, WAIFUWARS_NUMATTACKING, WAIFUWARS_NUMATTACKED]:
            print(j)
            _df[j] = df[j].loc[i[2][0]:i[2][1]].values.tolist()
        values = _df.values.tolist()
        # print("haha")
        # print([_df.columns.values.tolist()] + values)
        i[0].update([_df.columns.values.tolist()] + values)


def get_spreadsheet_from_drive(docid):
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        get_file_path("cred", "gsheets"), 
        scope
    )
    worksheets = []
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(docid)

    return spreadsheet

"""
Replace headers with the respective mapping.
"""
def correct_df_header(df, name_dict = qn_to_colnames):
    # print(df)
    columns = df.iloc[:1, :].values[0]
    df = df.iloc[1:, :]
    if name_dict is not None:
        # If column name exists in tha qn to col map, replace.
        df.columns = [name_dict[i] if i in name_dict.keys() else i for i in columns]
    else: 
        df.columns = columns
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
    # Combine all sheets to one single dataframe.
    for i, worksheet in enumerate(spreadsheet.worksheets()):
        worksheet_values = worksheet.get_all_values()

        if column_names is not None:
            exist_column_names = worksheet_values[0]
            missing_column_names = set(column_names) - set(exist_column_names)


        df = pd.DataFrame(worksheet_values)

        df = correct_df_header(df, name_dict)
        df_list.append(df) 

    output_df = pd.concat(df_list)

    # It is assumed that all worksheets have the same columns.
    if column_names is not None and missing_column_names is not None:
        output_df = output_df.assign(
            **{k: np.nan for k in missing_column_names}
        )
    return output_df

from difflib import SequenceMatcher
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
    print("hi", discord_name_from_df)
    _df = df.loc[df["Discord"] == discord_name_from_df]
    print(_df, _df["ArtPostOk"])
    return True if _df["ArtPostOk"].values[0] == "I agree" else False

def get_fuzzily_discord_handle(discord_name, df, get_uid = False):
    """
    Handles parsing of user-input Discord names and returns the name part
    """
    success_flag = False
    for index, row in df.iterrows():
        # print(row)
        # if index == 0:
        #     continue
        try:
            if re.match(r'[.]+\#[0-9]{4}', discord_name):
                if similar_in_num(row["Discord"], discord_name) == 1:
                    success_flag = True
                    break
            else:
                if similar_in_name(row["Discord"], discord_name) > 0.9:
                    success_flag = True
                    break
        except:
            pass
    if not success_flag: 
        return None
    return row["Discord"] if get_uid is False else row["uid"]

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

def set_up_weeklyprompts():
    df = get_inktober_from_gsheets()
    return df

def set_up_palette_particulars_csv():
    df = get_sheet_df_from_drive(os.getenv(DOCID_PALETTE_PARTICULARS_SURVEY))
    return df

import sys

"""
You can run code here to test the above functions.
"""
if __name__ == "__main__":
    # # for line in sys.stdin:
    # #     if 'q' == line.rstrip():
    # #         break

    # #     print(pretty_print_social_handle_wrapper(line))

    # # print("Exit")
    # # print(get_member_info_from_local_disk())
    # print(get_sheet_df_from_drive(DOCID_BIRTHDAY_TRACKER))
    # dummy_member_date = datetime(
    #     day=21,
    #     month=9,
    #     year=2000
    # )

    # dummy_curr_date = datetime(
    #     day=datetime.now().date().day,
    #     month=datetime.now().date().month,
    #     year=2000
    # )
    # print(dummy_curr_date - dummy_member_date)
    #print(similar_in_name("okai_iwen#1230", "okai_iwen#1230"))
    update_birthday_state_to_gsheets(None)


