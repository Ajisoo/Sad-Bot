import requests
from bs4 import BeautifulSoup
from globals import *
from random import randrange
import discord
import re
import shutil
import os
import random
import json
from PIL import Image
from fnmatch import fnmatch

import commands.leaderboard_util

async def cmd_ga_refresh(bot, message, args):
	if message.author.id not in [182707904367820800, 190253188262133761]:  # Us
		return

	bot.g_valid = False
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

	bot.g_valid = True
	await message.channel.send("All done")


async def cmd_guess(bot, message, args):
	if len(bot.g_answer) == 0:
		await message.channel.send("There's nothing to guess! Start with " + BOT_PREFIX + "guess_ability or guess_splash")
		return

	print(args)

	# Ignore emotes
	args = list(filter(lambda x: not (x.startswith(":") and x.endswith(":")), args))

	guess_arg = re.sub(r'[^a-z0-9]', '', " ".join(args).lower())
	if bot.g_answer == guess_arg:
		bot.g_answer_raw = ""
		bot.g_answer = ""
		await message.channel.send("<@" + str(message.author.id) + "> is Correct!")

		commands.leaderboard_util.update_leaderboards_file(message.author.id, bot.guess_type)


async def cmd_give_up(bot, message, args):
	if len(bot.g_answer) == 0:
		await message.channel.send("There's nothing to guess! Start with " + prefix + "guess_ability or guess_splash")
		return
	await message.channel.send("Answer was: " + bot.g_answer_raw)
	bot.g_answer_raw = ""
	bot.g_answer = ""


async def cmd_ga_start(bot, message, args):
	if not bot.g_valid:
		return
	len_file = open(GA_FOLDER + "!len.txt", "r")
	rand = randrange(int(len_file.readline()))
	len_file.close()
	info_file = open(GA_FOLDER + str(rand) + "info.txt", "r")
	if len(args) > 0 and (args[0].lower() == "c" or args[0].lower() == "champ" or args[0].lower() == "champion"):
		info_file.readline()
		bot.g_answer_raw = info_file.readline()
		bot.g_answer = re.sub(r'[^a-z0-9]', '', bot.g_answer_raw.lower())
		await message.channel.send("Guess the champion this ability belongs to!")
	elif len(args) > 0 and (args[0].lower() == "k" or args[0].lower() == "key" or args[0].lower() == "button"):
		info_file.readline()
		info_file.readline()
		bot.g_answer_raw = info_file.readline()
		bot.g_answer = re.sub(r'[^a-z0-9]', '', bot.g_answer_raw.lower())
		await message.channel.send("Guess the key (P, Q, W, E, R) this ability belongs to!")
	else:
		bot.g_answer_raw = info_file.readline()
		bot.g_answer = re.sub(r'[^a-z0-9]', '', bot.g_answer_raw.lower())
		await message.channel.send("Guess the name of this ability!")
	info_file.close()
	bot.guess_type = GA_LEADERBOARD_ID
	await message.channel.send(file=(discord.File(GA_FOLDER + str(rand) + "img.png")))


# ----------------------------------------------------------------------------------------------


#### GUESS SPLASH CONSTANTS #####

latest_version = None

versions_endpoint = 'https://ddragon.leagueoflegends.com/api/versions.json'
data_dragon_endpoint_base = 'https://ddragon.leagueoflegends.com/cdn/dragontail-'

dumpfile_name = GS_FOLDER + 'dump.tgz'
champ_splashes_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "splash" + os.path.sep
champ_loadingsplash_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "loading" + os.path.sep
latest_version_file = GS_FOLDER + "latest_version.txt"

temp_image_name = "tempCroppedSplash.jpg"

### GUESS SPLASH CONSTANTS END ###

async def cmd_gs_refresh(bot, message, args):
	if message.author.id not in [182707904367820800, 190253188262133761]:  # Us
		return
	
	# Get the latest patch number
	response = requests.get(versions_endpoint)
	
	open(latest_version_file, "a").close()

	global latest_version
	try:
		version = ""
		with open(latest_version_file, "r+") as f:
			version = f.readline().strip()

		if version != response.json()[0]:
			latest_version = response.json()[0]
			with open(latest_version_file, "w+") as f:
				f.write(latest_version)
		else:
			print("Latest version already gotten")
			await message.channel.send("Champ splashes are already refreshed!")
		
	except Exception as e:
		print("Getting latest version has failed: " + str(e))

	bot.g_valid = False

	# Create the data directory if not exists
	if not os.path.exists(GS_FOLDER):
		os.makedirs(GS_FOLDER)

	# Get the data dragon dump
	data_dragon_endpoint_full = data_dragon_endpoint_base + latest_version + ".tgz"
	print(data_dragon_endpoint_full)

	await message.channel.send("Loading champ splashes...")

	data_dump_response = requests.get(data_dragon_endpoint_full, stream=True)
	if response.status_code == 200:
		print("Getting data dragon dump...")
		with open(dumpfile_name, 'wb') as f:
			f.write(data_dump_response.raw.read())
		print("Done downloading data dump!")

		print("Unpacking data dump...")
		shutil.unpack_archive(dumpfile_name, GS_FOLDER)
		print("Done unpacking data dump!")

		# Remove tgz, dragonhead, languages, and lolpatch_*
		print("Removing extraneous files...")
		for file in os.listdir(GS_FOLDER):
			if fnmatch(file, "lolpatch*"):
				shutil.rmtree(GS_FOLDER + file, ignore_errors=True)
			elif fnmatch(file, "*.json") or fnmatch(file, "*.js") or fnmatch(file, "dump.tgz"):
				os.remove(GS_FOLDER + file)
		print("Removed extraneous files!")

		print("Done, champ splashes are ready now!")
		await message.channel.send("Champ splashes are ready now!")

	else:
		print("Error, here is response:" + str(response))
		await message.channel.send("Error: " + str(response))	
	
	bot.g_valid = True 


async def cmd_gs_start(bot, message, args):
	if not os.path.exists(champ_loadingsplash_folder):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	
	chosen_splash = random.choice(os.listdir(champ_loadingsplash_folder))

	# First get the champ + skin number (i.e. Aatrox_2 or Kaisa_3)
	# Then we match this against the data JSON to find the actual skin name

	champ_plus_skin_number = chosen_splash[:chosen_splash.find(".jpg")]

	champ_name, skin_number = champ_plus_skin_number.split("_")
	print(champ_name)
	print(skin_number)

	global latest_version
	if latest_version == None:
		try:
			with open(latest_version_file, "r") as f:
				latest_version = f.readline().strip()
		except Exception as e:
			print("Latest version file doesn't exist, please refresh")
			await message.channel.send("Latest version file doesn't exist, please refresh")
			return

	# Load the data JSON into memory 
	champ_data_folder = GS_FOLDER + os.path.sep + latest_version + os.path.sep + "data" + os.path.sep + "en_US" + os.path.sep
	if not os.path.exists(champ_data_folder):
		await message.channel.send("Champ data folder doesn't exist, ask admin to refresh")
		return

	json_data = None
	with open(champ_data_folder + os.path.sep + "champion" + os.path.sep + champ_name + ".json", "r", encoding="utf-8") as f:
		json_data = json.load(f)

	skins_array = json_data["data"][champ_name]["skins"]
	for skin in skins_array:
		if skin["num"] == int(skin_number):
			print(skin["name"])
			bot.g_answer_raw = skin["name"]
			bot.g_answer = re.sub(r'[^a-z0-9]', '', bot.g_answer_raw.lower())
			break

	im = Image.open(champ_loadingsplash_folder + chosen_splash)
	x, y = im.size
	
	left = random.randint(0, x / 2)
	right = left + x / 2
	top = random.randint(0, y - (x / 2))
	bottom = top + x / 2

	cropped_img = im.crop((left, top, right, bottom))

	cropped_img.save(temp_image_name, "jpeg")
	await message.channel.send(file=(discord.File(temp_image_name)))
	os.remove(temp_image_name)

	bot.guess_type = GS_LEADERBOARD_ID
	await message.channel.send("Guess the champion skin!")