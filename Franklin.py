
def get_franklin(bot, message_id):
	return bot.current_Franklins.get(message_id)


class Franklin:

	def __init__(self, bot, message_to_be_reacted_to, valid_reactions, functions, data):
		self.message = message_to_be_reacted_to
		self.data = data
		self.map = dict(zip(valid_reactions, functions))
		bot.current_Franklins[message_to_be_reacted_to.id] = self

	async def react(self, reaction, member):
		await self.message.remove_reaction(reaction, member)
		func = self.map.get(str(reaction))
		if func is not None:
			await func(self.data, member.id, self.message, str(reaction))