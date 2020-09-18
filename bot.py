import discord
import datetime
import asyncio
import random
import re

from data.bot_status import BotStatus
from commands import ga_util, leaderboard_util
from commands.tictactoe_util import cmd_tictactoe
from Franklin import get_franklin
from globals import *

client = discord.Client()
bot = BotStatus(client)


@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
	global bot

	if message.guild is None:
		return  #we are in PM

	if message.author == client.user:
		return  # we are ourself

	now = datetime.now()

	if message.author.status == discord.Status.dnd:
		await message.add_reaction(await message.guild.fetch_emoji(634171978420322335))

	if message.author.id in BIRTHDAYS.keys() and BIRTHDAYS[message.author.id][0] == now.month and BIRTHDAYS[message.author.id][1] == now.day:
		await message.add_reaction('🍰')

	args = []
	if message.content[:len(BOT_PREFIX)] == BOT_PREFIX:
		args = message.content[len(BOT_PREFIX):].split(' ')
		if len(args[0]) == 0:
			args = args[1:] if len(args) > 1 else []
	else:
		return

	if len(args) == 0:
		return

	args = [x.lower() for x in args]
	command = args[0].lower()
	args = args[1:] if len(args) > 1 else []

	if not bot.patch_message_sent and now.date() == PATCH_DAY.date():
		await message.channel.send(PATCH_MESSAGE_HEADER + PATCH_MESSAGE)
		bot.patch_message_sent = True

	if command == "help":
		await message.author.send(HELP_DEFAULT_MESSAGE)

	if command == 'ga_refresh':
		await ga_util.cmd_ga_refresh(bot, message, args)

	if command == 'ga_lb' or command == "lb":
		await message.channel.send(leaderboard_util.get_leaderboard())

	if command == 'ga_my_score' or command == "my_score":
		await message.channel.send(leaderboard_util.get_my_points(message.author.id))

	if command == 'guess_ability' or command == 'ga':
		if len(args) > 0 and args[0] == "refresh":
			await ga_util.cmd_ga_refresh(bot, message, args)
			return
		await ga_util.cmd_ga_start(bot, message, args)

	if command == 'guess' or command == 'g':
		await ga_util.cmd_ga_guess(bot, message, args)

	if command == 'giveup' or command == 'gu' or command == 'give_up':
		await ga_util.cmd_ga_give_up(bot, message, args)

	if command == 'roll':
		dice = args[0]

		if not re.match("d[1-9][0-9]*", dice):
			await message.channel.send("Use format `roll d<number>` to roll a die.")
			return

		die_number = int(dice[1:])
		rand = random.randint(1, die_number)

		await message.channel.send(f"<@{message.author.id}> rolled {rand}!")

	if command == 'tictactoe' or command == 'ttt':
		await cmd_tictactoe(bot, client.user, message, args)

	if command == 'bakamitai' or command == 'bm':
		try:
			vc = await message.author.voice.channel.connect()
		except Exception:
			pass
		vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=CONTENT_FOLDER + 'baka_mitai.mp3'))
		while vc.is_playing():
			await asyncio.sleep(1)
		# disconnect after the player has finished
		vc.stop()
		await vc.disconnect()

	if command == 'disconnect' or command == 'dc':
		await message.guild.voice_client.disconnect()

	if command == 'join':
		await message.author.voice.channel.connect()

	if command == 'patch_notes' or command == 'pn':
		await message.channel.send(PATCH_MESSAGE_HEADER + PATCH_MESSAGE)



@client.event
async def on_raw_reaction_add(payload):
	global bot

	if client.user.id == payload.user_id:  # Don't respond to your own reactions
		return

	reaction = payload.emoji
	message_id = payload.message_id
	franklin = get_franklin(bot, message_id)

	if reaction.is_custom_emoji():
		processed_emoji = client.get_emoji(reaction.id)
	else:
		processed_emoji = reaction.name

	if franklin is not None:
		await franklin.react(processed_emoji, payload.member)


key_file = open("bot.key", "r")
key = key_file.readline().strip()
key_file.close()

client.run(key)
