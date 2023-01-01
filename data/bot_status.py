import datetime as dt

import discord
from discord.ext import tasks, commands as c

from commands import message_guess

class BotStatus(c.Cog):

	def __init__(self, discord_client, guild):
		self.client = discord_client
		self.guild = guild
		self.g_valid = True
		self.g_answer = ""
		self.g_answer_raw = ""
		self.patch_message_sent = False
		self.essay_mode_on = False
		self.essay_mode_minimum = 0
		self.current_Franklins = {}
		self.listener = None
		self.guess_type = ""
		self.start_date = None
		self.roll_user_data = None
		self.rarity_emoji_ids = {}
		self.active_trades = {}

		for emoji in discord_client.emojis:
			if emoji.name in ['epic', 'legendary', 'mythic', 'ultimate']:
				self.rarity_emoji_ids[emoji.name] = emoji.id
				if len(self.rarity_emoji_ids) >= 4:
					break
		self.umq_last_song_fn = None
		self.umq_last_song_ts = None
