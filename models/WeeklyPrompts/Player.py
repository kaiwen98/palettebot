NUM_WEEKS = 13
MESSAGE_ID_TYPES = ["PENDING_APPROVAL", "APPROVED", "REJECTED"]

class Player():
  def __init__(self, discord_name, column_from_gspread_worksheet):
    self.discord_name = discord_name

    self.column_from_gspread_worksheet = column_from_gspread_worksheet

    self.week_to_num_submitted_artworks: list = [
      0 for i in range(NUM_WEEKS)
    ]
    
    # Example message id: 1013124530690084875
    self.message_id_lists: dict = {
      type: set([]) for type in MESSAGE_ID_TYPES
    }

  def set_score_by_encoding(self, encoding, week):
    # 0000000000000
    for week in range(1, NUM_WEEKS + 1):
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
    return {k: ";".join(self.message_id_lists[k]) for k in MESSAGE_ID_TYPES}

  def set_messages_id_lists_by_encoding(self, message_id_type, encoding):
    self.message_id_lists[message_id_type] = encoding.split(";")
    pass

  def append_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].add(str(message_id))

  def remove_message_id_to_list_by_type(self, message_id, message_id_type):
    self.message_id_lists[message_id_type].remove(str(message_id))

