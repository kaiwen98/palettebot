from utils.commons import (
  GSHEET_BIRTHDAY_COLUMN_STATE,
  GSHEET_COLUMN_BIRTHDAY,
  GSHEET_COLUMN_DISCORD,
  GSHEET_COLUMN_NAME,
  GSHEET_COLUMNS_MESSAGE_STATES,
  GSHEET_INKTOBER_COLUMN_STATE,
  GSHEET_INKTOBER_COLUMNS_MESSAGE_STATES,
  GSHEET_WAIFUWARS_COLUMN_STATE_NUMATTACKED,
  GSHEET_WAIFUWARS_COLUMNS_MESSAGE_STATES,
  GSHEET_WEEKLYPROMPT_COLUMN_APPROVED, 
  GSHEET_WEEKLYPROMPT_COLUMN_STATE, 
  GSHEET_WEEKLYPROMPT_COLUMN_PENDING_APPROVAL, 
  GSHEET_WEEKLYPROMPT_COLUMN_REJECTED,
  GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES,
  NUM_DAYS,
  NUM_WEEKS,
)

class Player():
  def __init__(self, row_from_gspread_worksheet):
    self.attributes = row_from_gspread_worksheet

    self.week_to_num_submitted_artworks: list = [
      0 for i in range(NUM_WEEKS)
    ]

    self.day_to_submitted_artworks: list = [
      0 for i in range(NUM_DAYS)
    ]
    
    # Example message id: 1013124530690084875
    self.message_id_lists: dict = {
      type: set([]) for type in GSHEET_COLUMNS_MESSAGE_STATES
    }
    
    for week in range(NUM_WEEKS):
      self.set_weeklyprompt_scores_by_encoding(self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_STATE], week)

    messages = {
      k: self.attributes[k] \
      if k in self.attributes.index else "" \
      for k in GSHEET_COLUMNS_MESSAGE_STATES
    }

    for type in GSHEET_WEEKLYPROMPT_COLUMNS_MESSAGE_STATES:
      self.set_messages_id_lists_by_encoding(type, messages[type])

  def set_weeklyprompt_scores_by_encoding(self, encoding, week):
    # 0000000000000
    self.week_to_num_submitted_artworks[week] = int(encoding.split(";")[week])
    self.day_to_submitted_artworks[week] = int(encoding.split(";")[week])

  def get_weeklyprompt_scores_to_encoding(self):
    return ';'.join(
      map(
        lambda x: str(x),
        self.week_to_num_submitted_artworks
      )
    )

  def set_inktober_scores_by_encoding(self, encoding, week):
    # 0000000000000
    self.day_to_submitted_artworks[week] = int(encoding.split(";")[week])

  def get_inktober_scores_to_encoding(self):
    return ';'.join(
      map(
        lambda x: str(x),
        self.day_to_submitted_artworks
      )
    )

  def set_birthday_state(self, birthday_state):
    self.attributes[GSHEET_BIRTHDAY_COLUMN_STATE] = birthday_state

  def credit_inktober_score_at_week(self, week):
    self.day_to_submitted_artworks[week - 1] = 1

  def increment_weeklyprompt_score_at_week(self, week, increment):
    self.week_to_num_submitted_artworks[week - 1] += increment

  def get_messages_id_lists_to_encoding(self):
    return {k: ";".join(self.message_id_lists[k])[1:] for k in GSHEET_INKTOBER_COLUMNS_MESSAGE_STATES}

  def set_messages_id_lists_by_encoding(self, message_id_type, encoding):
    self.message_id_lists[message_id_type] = set(filter(lambda x: x != '', encoding.split(";")))
    pass

  def append_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].add(str(message_id))

  def remove_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].remove(str(message_id))

  def set_birthday_from_encoding(self, birthday):
    pass

  def export_to_df_row(self):
    output_df_row = self.attributes
    
    # Update messages
    encoded_message_id_lists = self.get_messages_id_lists_to_encoding()

    output_df_row = {
      **output_df_row,
      **encoded_message_id_lists
    } 

    # Update Scores
    output_df_row[GSHEET_WEEKLYPROMPT_COLUMN_STATE] = self.get_weeklyprompt_scores_to_encoding()
    output_df_row[GSHEET_INKTOBER_COLUMN_STATE] = self.get_inktober_scores_to_encoding()

    return output_df_row
