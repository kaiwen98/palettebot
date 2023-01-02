"""
Handles Upload of contents to Google Drive.
If you are not me, you should not temper with this.
Always try to use your local directory when you are developing. In which case, look at the local_disk functions.
"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime
from utils.constants import DRIVE__PALETTE_REP_TRACKER
from utils.utils import get_file_path

gauth = GoogleAuth()
print(
    get_file_path("cred", "gdrive", "credentials.json")
)

gauth.LoadCredentialsFile(
    "./credentials.json" if os.getenv("ENV") == "production" \
    else get_file_path("cred", "gdrive", "credentials.json")  
)

drive = GoogleDrive(gauth)  

def upload_to_gdrive(upload_file_list: list):
    for upload_file in upload_file_list:
        gfile = drive.CreateFile({'parents': [{'id': DRIVE__PALETTE_REP_TRACKER}]})
        # Read file and set it as the content of this instance.
        gfile.SetContentFile(upload_file)
        gfile.Upload() # Upload the file.

    file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(DRIVE__PALETTE_REP_TRACKER)}).GetList()
    file_list.sort(key = lambda x: x['createdDate'])
    print(file_list[-1]['createdDate'])
    return file_list[-1]['webContentLink']

