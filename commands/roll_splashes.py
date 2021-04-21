import os
from globals import *
from random import randrange
import discord
import re
import os
import random
import json
from PIL import Image

### Globals ###

latest_version = None

champ_splashes_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "splash" + os.path.sep
champ_loadingsplash_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "loading" + os.path.sep
latest_version_file = GS_FOLDER + "latest_version.txt"

temp_image_name = "tempCroppedSplash.jpg"

### End Globals ###

async def cmd_splash_roll(bot, message, args):
	if not os.path.exists(champ_loadingsplash_folder):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	
	chosen_splash = random.choice(os.listdir(champ_loadingsplash_folder))

	# First get the champ + skin number (i.e. Aatrox_2 or Kaisa_3)
	# Then we match this against the data JSON to find the actual skin name
	champ_plus_skin_number = chosen_splash[:chosen_splash.find(".jpg")]

	champ_name, skin_number = champ_plus_skin_number.split("_")

	# Confirm latest version exists
	global latest_version
	if latest_version == None:
		try:
			with open(latest_version_file, "r") as f:
				latest_version = f.readline().strip()
		except Exception as e:
			print("Latest version file doesn't exist, please refresh")
			await message.channel.send("Latest version file doesn't exist, please refresh")
			return
	
	champ_data_folder = GS_FOLDER + os.path.sep + latest_version + \
		os.path.sep + "data" + os.path.sep + "en_US" + os.path.sep
	if not os.path.exists(champ_data_folder):
		await message.channel.send("Champ data folder doesn't exist, ask admin to refresh")
		return

	json_data = None
	with open(champ_data_folder + os.path.sep + "champion" + os.path.sep + champ_name + ".json", "r", encoding="utf-8") as f:
		json_data = json.load(f)

	# See guess_util.py for explanation of why we traverse this array.
	skins_array = json_data["data"][champ_name]["skins"]
	full_skin_name = None
	for skin in skins_array:
		if skin["num"] == int(skin_number):
			print(skin["name"])

			if skin["name"] == "default":
				full_skin_name = champ_name
			else:
				full_skin_name = skin["name"]
			break
	
	# Pick one of 4 pieces of the splash
	im = Image.open(champ_loadingsplash_folder + chosen_splash)
	x, y = im.size

	left = random.choice([0, x / 2])
	right = left + x / 2
	top = random.choice([0, y / 2])
	bottom = top + y / 2

	cropped_img = im.crop((left, top, right, bottom))

	cropped_img.save(temp_image_name, "jpeg")
	await message.channel.send(file=(discord.File(temp_image_name)))
	os.remove(temp_image_name)

	await message.channel.send("This is " + full_skin_name + "!")
