class BotStatus:

	def __init__(self, discord_client):
		self.client = discord_client
		self.g_valid = True
		self.g_answer = ""
		self.g_answer_raw = ""
		self.patch_message_sent = False
		self.current_Franklins = {}
		self.listener = None
		self.guess_type = ""
		self.start_date = None
		self.roll_user_data = None
		self.umq_last_song_fn = None
		self.umq_last_song_ts = None
