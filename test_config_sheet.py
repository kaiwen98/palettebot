from models.ConfigurationSheet import ConfigurationSheet
from utils.utils import get_today_datetime, get_week_from_datetime
import json

if __name__ == "__main__":
    c = ConfigurationSheet()
    c.get_spreadsheet()
    c.process_prompt()
    
    gid = c.getGidFromGdriveUrl("https://drive.google.com/file/d/1P0j8kZVO8kQ3yf6HUBR839alHuJtvBHd/view")
    c.downloadImageByGid(gid)
    c.process_config()
    print(json.dumps(c.config, indent = 2))
    print(json.dumps(c.semester_period, indent = 2))
    print(json.dumps(c.prompts, indent = 2))

    print(get_week_from_datetime(get_today_datetime()))