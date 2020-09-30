import requests
from bs4 import BeautifulSoup
from globals import *
from random import randrange
import discord
import re

import commands.leaderboard_util


async def cmd_ga_refresh(bot, message, args):
	if message.author.id not in [182707904367820800, 190253188262133761]:  # Us
		return

	bot.ga_valid = False
	await message.channel.send("Refreshing content. Expect failing commands until done.")

	r = requests.get(GA_WEBSITE)
	soup = BeautifulSoup(r.content, "html.parser")

	ability_list = soup.find("div", {"class": "ability-list"}).find_all("a", {"class": "ability-list__item"})
	counter = 0
	for ability in ability_list:
		champ_name = ability.find("img", {"class": "ability-list__item__champ"})["champ"].replace("\n", " ")
		image = ability.find("img", {"class": "ability-list__item__pic"})["src"]
		ability_name = str(ability.find("span", {"class": "ability-list__item__name"}).contents[0]).strip().replace(
			"\n", " ")
		ability_key = ability.find("div", {"class": "ability-list__item__keybind"}).text.replace("\n", " ")
		if ability_key is None or len(ability_key.strip()) == 0:
			ability_key = "P"

		with open(GA_FOLDER + str(counter) + "img.png", "wb+") as image_file:
			image_file.write(requests.get(GA_BASE_WEBSITE + image).content)

		with open(GA_FOLDER + str(counter) + "info.txt", "w+") as text_file:
			text_file.write(ability_name + "\n" + champ_name + "\n" + ability_key)

		counter += 1

	with open(GA_FOLDER + "!len.txt", "w+") as length_file:
		length_file.write(str(counter))

	bot.ga_valid = True
	await message.channel.send("All done")


async def cmd_ga_guess(bot, message, args):
	if len(bot.ga_answer) == 0:
		await message.channel.send("There's no ability to guess! Start with " + BOT_PREFIX + "guess_ability")
		return

	print(args)

	# Ignore emotes
	args = list(filter(lambda x: not (x.startswith(":") and x.endswith(":")), args))

	guess_arg = re.sub(r'[^a-z0-9]', '', " ".join(args).lower())
	if bot.ga_answer == guess_arg:
		bot.ga_answer_raw = ""
		bot.ga_answer = ""
		await message.channel.send("<@" + str(message.author.id) + "> is Correct!")

		commands.leaderboard_util.update_leaderboards_file(message.author.id)
		await cmd_ga_start(bot, message, args)


async def cmd_ga_give_up(bot, message, args):
	if len(bot.ga_answer) == 0:
		await message.channel.send("There's no ability to guess! Start with " + prefix + "guess_ability")
		return
	await message.channel.send("Answer was: " + bot.ga_answer_raw)
	bot.ga_answer_raw = ""
	bot.ga_answer = ""
	await cmd_ga_start(bot, message, args)


async def cmd_ga_start(bot, message, args):
	if not bot.ga_valid:
		return
	len_file = open(GA_FOLDER + "!len.txt", "r")
	rand = randrange(int(len_file.readline()))
	len_file.close()
	info_file = open(GA_FOLDER + str(rand) + "info.txt", "r")
	if len(args) > 0 and (args[0].lower() == "c" or args[0].lower() == "champ" or args[0].lower() == "champion"):
		info_file.readline()
		bot.ga_answer_raw = info_file.readline()
		bot.ga_answer = re.sub(r'[^a-z0-9]', '', bot.ga_answer_raw.lower())
		await message.channel.send("Guess the champion this ability belongs to!")
	elif len(args) > 0 and (args[0].lower() == "k" or args[0].lower() == "key" or args[0].lower() == "button"):
		info_file.readline()
		info_file.readline()
		bot.ga_answer_raw = info_file.readline()
		bot.ga_answer = re.sub(r'[^a-z0-9]', '', bot.ga_answer_raw.lower())
		await message.channel.send("Guess the key (P, Q, W, E, R) this ability belongs to!")
	else:
		bot.ga_answer_raw = info_file.readline()
		bot.ga_answer = re.sub(r'[^a-z0-9]', '', bot.ga_answer_raw.lower())
		await message.channel.send("Guess the name of this ability!")
	info_file.close()
	await message.channel.send(file=(discord.File(GA_FOLDER + str(rand) + "img.png")))