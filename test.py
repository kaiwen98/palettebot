from datetime import datetime
from config_loader import load_config
from models.DiscordBot import DiscordBot
from models.Player import Player
from utils.constants import GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL, GSHEET_WEEKLYPROMPT_COLUMN_REJECTED
from utils.utils import get_file_path, get_rank_emoji, get_week_from_datetime
from controller.excelHandler import get_weeklyprompts_from_gsheets, update_birthday_state_to_gsheets, update_weeklyprompt_state_to_gsheets

def test2():
  from utils.messages import (
    MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE
  )

  import pystache

  print(
    pystache.render(
      MESSAGE_WEEKLYPROMPT_SCORE_MESSAGE,
      {
        "game": "Gaimu",
        "role": "@sdfd",
        "prompts": [
          {
            "id": 1,
            "emoji": ":happy:",
            "prompt": "Happy"
          }
        ],
        "scores": [
          {
            "id": 1,
            "score": 8,
            "name": "Looi Kai Wen",
            "emoji": get_rank_emoji(1)
          }
        ]
      }
    )
  )



def test1():
  player = list(DiscordBot().players.items())[5][1]
  player.increment_weeklyprompt_score_at_week(2, 1)
  player.increment_weeklyprompt_score_at_week(2, 1)
  player.add_message_id_to_set_by_type(3434324324, GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, {"a": 5})
  player.add_message_id_to_set_by_type(3434324325, GSHEET_WEEKLYPROMPT_COLUMN_APPROVED)
  player.add_message_id_to_set_by_type(3434324327, GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL)
  player.add_message_id_to_set_by_type(3434324328, GSHEET_WEEKLYPROMPT_COLUMN_REJECTED)
  player.move_message_id_across_types(3434324324, GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, GSHEET_WEEKLYPROMPT_COLUMN_REJECTED)
  player.move_message_id_across_types(3434324325, GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, GSHEET_WEEKLYPROMPT_COLUMN_REJECTED)
  print(
    player.get_weeklyprompt_scores_to_encoding()
  )

  print(
    player.get_messages_id_lists_to_encoding()
  )

  print(
    player.message_id_sets
  )

  print(
    player.weeklyprompts_week_to_num_submitted_artworks
  )

  DiscordBot().update_players_to_db()


  # df_row = \
    # player.export_to_df_row()

  # df.iloc[1] = df_row

  # # print(df)

  # update_weeklyprompt_state_to_gsheets(df)

  print("done")

  # print(
    # get_week_from_curr_datetime(
      # datetime.today()
    # )
  # )


if __name__ == "__main__":
  load_config('local')
  print(
    get_file_path("cred", "gsheets")
  )

  # print(
    # update_birthday_state_to_gsheets(None)
  # )

  # player = Player(None)
  # player.increment_score_at_week(2, 1)
  # player.append_message_id_to_list_by_type(3434324324, "APPROVED")
  # player.append_message_id_to_list_by_type(3434324325, "APPROVED")
  # print(
    # player.get_weekly_scores_from_encoding()
  # )

  # print(
    # player.get_messages_id_lists_to_encoding()
  # )

  #df = get_weeklyprompts_from_gsheets()
  #player = Player(df.iloc[1]) 




  bot = DiscordBot().bot

  @bot.event
  async def on_ready():
    DiscordBot().set_up_after_run()
    test1()
    #test2()

  DiscordBot().run()


