from controller.excelHandler import (
  INKTOBER_STATE, 
  WAIFUWARS_NUMATTACKED, 
  WAIFUWARS_NUMATTACKING
)

from utils.commons import (
  APPROVED,
  GSHEET_COLUMN_BIRTHDAY,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_NAME,
  GSHEET_INKTOBER_STATE,
  GSHEET_WAIFUWARS_STATE_NUMATTACKED,
  GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, 
  GSHEET_WEEKLYPROMPT_STATE, 
  GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL, 
  GSHEET_WEEKLYPROMPT_COLUMN_REJECTED,
  NUM_WEEKS,
  PENDING_APPROVAL,
  REJECTED
)

MESSAGE_ID_TYPES = [PENDING_APPROVAL, APPROVED, REJECTED]
class Player():
  def __init__(self, row_from_gspread_worksheet):
    print(row_from_gspread_worksheet)
    self.attributes = row_from_gspread_worksheet

    self.week_to_num_submitted_artworks: list = [
      0 for i in range(NUM_WEEKS)
    ]
    
    # Example message id: 1013124530690084875
    self.message_id_lists: dict = {
      type: set([]) for type in MESSAGE_ID_TYPES
    }
    
    for week in range(NUM_WEEKS):
      self.set_score_by_encoding(self.attributes[GSHEET_WEEKLYPROMPT_STATE], week)

    messages = {
      PENDING_APPROVAL: self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL],
      APPROVED: self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_APPROVED],
      REJECTED: self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_REJECTED]
    }

    for type in MESSAGE_ID_TYPES:
      self.set_messages_id_lists_by_encoding(type, messages[type])

  def set_score_by_encoding(self, encoding, week):
    # 0000000000000
    self.week_to_num_submitted_artworks[week] = int(encoding[week])

  def get_weekly_scores_from_encoding(self):
    return ''.join(
      map(
        lambda x: str(x),
        self.week_to_num_submitted_artworks
      )
    )

  def increment_score_at_week(self, week, increment):
    self.week_to_num_submitted_artworks[week - 1] += increment

  def get_messages_id_lists_to_encoding(self):
    return {k: ";".join(self.message_id_lists[k])[1:] for k in MESSAGE_ID_TYPES}

  def set_messages_id_lists_by_encoding(self, message_id_type, encoding):
    self.message_id_lists[message_id_type] = set(filter(lambda x: x != '', encoding.split(";")))
    pass

  def append_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].add(str(message_id))

  def remove_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].remove(str(message_id))

