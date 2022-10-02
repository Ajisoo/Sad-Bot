import threading

from discord import message


def get_franklin(bot, message_id):
    return bot.current_Franklins.get(message_id)


def remove_franklin(bot, message_id):
    try:
        del bot.current_Franklins[message_id]
    except:
        pass


class Franklin:
    def __init__(
        self,
        bot,
        message_to_be_reacted_to,
        valid_reactions,
        functions,
        data,
        lifespan=180.0,
        remove_valid_reactions=True,
    ):
        self.message = message_to_be_reacted_to
        self.data = data
        self.map = dict(zip(valid_reactions, functions))
        self.remove_valid_reactions = remove_valid_reactions
        bot.current_Franklins[message_to_be_reacted_to.id] = self
        t = threading.Timer(
            lifespan, remove_franklin, (bot, message_to_be_reacted_to.id)
        )
        t.start()

    async def react(self, reaction, member):
        func = self.map.get(str(reaction))
        if self.remove_valid_reactions or func is None:
            await self.message.remove_reaction(reaction, member)
        if func is not None:
            await func(self.data, member.id, self.message, str(reaction))

    async def remove_reaction(
        self, reaction
    ):  # only add_react returns a member in payload
        func = self.map.get(str(reaction))
        if func is not None:
            await func(self.data, 0, self.message, str(reaction))
