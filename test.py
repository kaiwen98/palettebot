from config_loader import load_config
from models.WeeklyPrompts.Player import Player
from utils.utils import get_file_path
from controller.excelHandler import update_birthday_state_to_gsheets


if __name__ == "__main__":
  load_config('local')
  print(
    get_file_path("cred", "gsheets")
  )

  # print(
    # update_birthday_state_to_gsheets(None)
  # )

  player = Player("jimmy", None)
  player.increment_score_at_week(2, 1)
  player.append_message_id_to_list_by_type(3434324324, "APPROVED")
  player.append_message_id_to_list_by_type(3434324325, "APPROVED")
  print(
    player.get_weekly_scores_from_encoding()
  )

  print(
    player.get_messages_id_lists_to_encoding()
  )
