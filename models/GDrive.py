from ..utils.constants import DIR_OUTPUT
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from google.oauth2 import service_account
import re
import os

CREDENTIALS_FILE_PATH = os.path.join(os.getcwd(), "creds", "gdrive", "credentials.json")
SETTINGS_FILE_PATH = os.path.join(os.getcwd(), "settings.yml")

class GDrive():
    def __init__(self):
        gauth = GoogleAuth(settings_file=SETTINGS_FILE_PATH)
        gauth.LoadCredentialsFile(
        #    CREDENTIALS_FILE_PATH
        )

        self.drive = GoogleDrive(gauth)

    def getGidFromGdriveUrl(url):
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
    
    def retrieve(self, url):

        id = self.getGidFromGdriveUrl(url)
        """ Retrieve an image given the gdrive id and store locally.        

        Args:
            id (string): The gdrive id.

        Returns:
            string: The path to the locally stored file.
        """

        fileObj = self.drive.CreateFile({'id': id})

        # Clean file name.
        filename = fileObj['title'].replace(":", "").strip()



        # Parsing {{ext}} from application/{{ext}}
        fileExt = fileObj['mimeType'].split('/')[1]

        # Check if uploaded with ext in name
        ext = os.path.splitext(filename)[-1].lower()
        print(ext)

        if '.' not in ext:
            filename += f".{fileExt}"

        # Editable, if you wish to use cached photos.
        if not os.path.exists(os.path.join(DIR_OUTPUT, "images", f"{filename}")):        
            fileObj.GetContentFile(os.path.join(DIR_OUTPUT, "images", f"{filename}"))

        return os.path.join(DIR_OUTPUT, f"{filename}")