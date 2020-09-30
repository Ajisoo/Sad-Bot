class BotStatus:

	def __init__(self, discord_client):
		self.client = discord_client
		self.ga_valid = True
		self.gs_valid = True
		self.ga_answer = ""
		self.ga_answer_raw = ""
		self.patch_message_sent = False
		self.current_Franklins = {}
		self.listener = None
