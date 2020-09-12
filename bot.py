import discord
import datetime
import asyncio
import random
import re

import refresh

prefix = "$"

client = discord.Client()

birthdays = {225822313550053376: [3, 14], 167090536602140682: [7, 21], 191597928090042369: [8, 3], 193550776340185088: [11, 20], 363197965306953730: [9, 2], 182707904367820800: [11,2]}

guess_answer = ""
guess_answer_raw = ""

@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	global guess_answer
	global guess_answer_raw
	if message.guild is None:
		return  #we are in PM

	if message.author == client.user:
		return  # we are ourself

	now = datetime.datetime.now()

	if message.author.status == discord.Status.dnd:
		await message.add_reaction(await message.guild.fetch_emoji(634171978420322335))

	if message.author.id in birthdays.keys() and birthdays[message.author.id][0] == now.month and birthdays[message.author.id][1] == now.day:
		await message.add_reaction('🍰')

	args = []
	if message.content[:len(prefix)] == prefix:
		args = message.content[len(prefix):].split(' ')
		if len(args[0]) == 0:
			args = args[1:] if len(args) > 1 else []
	else:
		return

	if len(args) == 0:
		return

	args = [x.lower() for x in args]
	command = args[0].lower()
	args = args[1:] if len(args) > 1 else []

	if command == "help":
		await message.author.send("😠 no help for you! 😠")

	if command == ">:(":
		await message.guild.get_member(client.user.id).edit(nick=">:(")
		# await message.channel.send(">:(")
		await message.channel.send(file=discord.File('angry.png'))
		await asyncio.sleep(5)
		await message.guild.get_member(client.user.id).edit(nick=":(")

	if command == 'refresh':
		await refresh.cmd_refresh(message, args)

	if command == 'guessability' or command == 'ga':
		len_file = open(refresh.data_folder + "!len.txt", "r")
		rand = random.randrange(int(len_file.readline()))
		len_file.close()
		info_file = open(refresh.data_folder + str(rand) + "info.txt", "r")
		if len(args) > 0 and (args[0].lower() == "c" or args[0].lower() == "champ" or args[0].lower() == "champion"):
			info_file.readline()
			guess_answer_raw = info_file.readline()
			guess_answer = re.sub(r'[^a-z0-9]', '', guess_answer_raw.lower())
			await message.channel.send("Guess the champion this ability belongs to!")
		elif len(args) > 0 and (args[0].lower() == "k" or args[0].lower() == "key" or args[0].lower() == "button"):
			info_file.readline()
			info_file.readline()
			guess_answer_raw = info_file.readline()
			guess_answer = re.sub(r'[^a-z0-9]', '', guess_answer_raw.lower())
			await message.channel.send("Guess the key (P, Q, W, E, R) this ability belongs to!")
		else:
			guess_answer_raw = info_file.readline()
			guess_answer = re.sub(r'[^a-z0-9]', '', guess_answer_raw.lower())
			await message.channel.send("Guess the name of this ability!")
		info_file.close()
		await message.channel.send(file=(discord.File(refresh.data_folder + str(rand) + "img.png")))

	if command == 'guess' or command == 'g':
		if len(guess_answer) == 0:
			await message.channel.send("There's no ability to guess! Start with " + prefix + "guess_ability")
			return

		guess_arg = re.sub(r'[^a-z0-9]', '', " ".join(args).lower())
		if guess_answer == guess_arg:
			guess_answer_raw = ""
			guess_answer = ""
			await message.channel.send("<@" + str(message.author.id) + "> is Correct!")

	if command == 'giveup' or command == 'gu':
		if len(guess_answer) == 0:
			await message.channel.send("There's no ability to guess! Start with " + prefix + "guess_ability")
			return
		await message.channel.send("Answer was: " + guess_answer_raw)
		guess_answer_raw = ""
		guess_answer = ""


key_file = open("bot.key", "r")
key = key_file.readline().strip()
key_file.close()

client.run(key)
