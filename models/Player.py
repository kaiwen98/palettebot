from utils.constants import (
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
  PAYLOAD_PARAMS,
)

import json

class Player():
  def __init__(self, row_from_gspread_worksheet):
    self.attributes = row_from_gspread_worksheet

    self.weeklyprompts_week_to_num_submitted_artworks: dict = {
      i: 0 for i in range(NUM_WEEKS)
    }

    self.inktober_day_to_submitted_artworks: dict = {
      i: 0 for i in range(NUM_DAYS)
    }
    
    # Example message id: 1013124530690084875
    self.message_id_sets: dict = {
      type: {} for type in GSHEET_COLUMNS_MESSAGE_STATES
    }
    print(self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_STATE]) 
    # Configure weekly prompt scores
    for week in range(NUM_WEEKS):
      self.set_weeklyprompt_scores_by_encoding(
        self.attributes[GSHEET_WEEKLYPROMPT_COLUMN_STATE], 
        week)

    for day in range(NUM_DAYS):
      self.set_inktober_scores_by_encoding(self.attributes[GSHEET_INKTOBER_COLUMN_STATE], day)

    messages = {
      k: self.attributes[k] \
      if k in self.attributes.index else "" \
      for k in GSHEET_COLUMNS_MESSAGE_STATES
    }
    
    # Configure message states
    for type in GSHEET_COLUMNS_MESSAGE_STATES:
      self.set_messages_id_lists_by_encoding(type, messages[type])

  """
  WeeklyPrompts
  """

  def set_weeklyprompt_scores_by_encoding(self, encoding, week):
    self.set_map_by_encoding(
      self.weeklyprompts_week_to_num_submitted_artworks,
      encoding, 
      week
    )

  def get_weeklyprompt_scores_to_encoding(self):
    return ';'.join(
      map(
        lambda x: str(x),
        self.weeklyprompts_week_to_num_submitted_artworks
      )
    )

  def increment_weeklyprompt_score_at_week(self, week, increment):
    self.weeklyprompts_week_to_num_submitted_artworks[week] += increment

  def get_weeklyprompt_scores_at_week(self, week):
    return self.weeklyprompts_week_to_num_submitted_artworks[week]

  def get_weeklyprompt_scores_sum(self):
    return sum(self.weeklyprompts_week_to_num_submitted_artworks.values())

  """
  Inktober
  """

  def get_inktober_scores_to_encoding(self):
    return ';'.join(
      map(
        lambda x: str(x),
        self.inktober_day_to_submitted_artworks
      )
    )


  def set_inktober_scores_by_encoding(self, encoding, day):
    # 0000000000000
    self.set_map_by_encoding(
      self.inktober_day_to_submitted_artworks,
      encoding, 
      day
    )

  def credit_inktober_score_at_week(self, week):
    self.inktober_day_to_submitted_artworks[week] = 1

  def get_inktober_scores_at_week(self, day):
    return self.inktober_day_to_submitted_artworks[day]

  def get_inktober_scores_sum(self):
    return sum(self.inktober_day_to_submitted_artworks.values())

  """
  Messages
  """

  def get_messages_id_lists_to_encoding(self):
    return {k: json.dumps(self.message_id_sets[k]) for k in GSHEET_COLUMNS_MESSAGE_STATES}

  def set_messages_id_lists_by_encoding(self, message_id_type, encoding):
    payload = json.loads(encoding) if len(encoding) else {}
    self.message_id_sets[message_id_type] = payload

  def add_message_id_to_set_by_type(self, message_id, message_id_type, payload={}):
    print(message_id_type)
    print(message_id)
    print(payload)
    self.message_id_sets[message_id_type][message_id] = payload

  def pop_message_id_from_set_by_type(self, message_id, message_id_type):
    payload = self.message_id_sets[message_id_type].pop(message_id)
    return message_id, payload

  def move_message_id_across_types(self, message_id, src_message_id_type, dest_message_id_type):
    temp = self.pop_message_id_from_set_by_type(message_id, src_message_id_type)
    self.add_message_id_to_set_by_type(temp[0], dest_message_id_type, temp[1])

  """
  Birthday
  """

  def set_birthday_from_encoding(self, birthday):
    pass

  def set_birthday_state(self, birthday_state):
    self.attributes[GSHEET_BIRTHDAY_COLUMN_STATE] = birthday_state

  """
  Export
  """

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

  """
  Utils
  """

  def set_map_by_encoding(self, map, encoding, index):
    map[index] = int(encoding.split(";")[index])
