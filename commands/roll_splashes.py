import os
from globals import *
from random import randrange
import discord
import re
import os
import random
import json
import bigjson
from numpy.random import choice
from PIL import Image

### Globals ###

latest_version = None

champ_splashes_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "splash" + os.path.sep
champ_loadingsplash_folder = GS_FOLDER + os.path.sep + "img" + os.path.sep + "champion" + os.path.sep + "loading" + os.path.sep
latest_version_file = GS_FOLDER + "latest_version.txt"

temp_image_name = "tempCroppedSplash.jpg"

percentages = None
rolls = None
id_to_alias_map = None
### End Globals ###

async def cmd_splash_roll(bot, message, args):
	if not os.path.exists(champ_loadingsplash_folder):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	if not os.path.exists(RS_ID_TO_ALIAS_MAPPINGS_FILE) or not os.path.exists(GS_FOLDER + 'rarity-dist.json'):
		print("RARITY DIST OR CHAMPION SUMMARY DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Champs can't be rolled right now. Please ask an admin to refresh the champ splashes!")
		return

	'''
		1. Pick a random thing out of the rarity-dist
		2. The 3 rightmost numbers are the skin number
		3. All numbers left of that are the champion ID
		4. Use champion-summary.json to get the Alias from ID
		5. Combine <Alias_SkinNumber> to get the jpg
		6. Query skins.json to get full skin name and description
	'''
	global percentages, rolls 
	if percentages == None or rolls == None:
		with open(GS_FOLDER + 'rarity-dist.json', 'r') as f:
			rarity_dist = json.load(f)
			loot_pools = [(v['percentage'], v['rolls']) for v in rarity_dist.values()]
			percentages, rolls = [list(t) for t in zip(*loot_pools)]

	res_index = choice(len(rolls), p=percentages)
	chosen_pool = rolls[res_index]

	full_champ_id = choice(chosen_pool)
	champ_id, skin_number = [full_champ_id // 1000, full_champ_id % 1000]
	
	global id_to_alias_map
	if id_to_alias_map == None:
		with open(RS_ID_TO_ALIAS_MAPPINGS_FILE, "r") as f:
			id_to_alias_map = json.load(f)
	
	champ_alias = id_to_alias_map[str(champ_id)]

	chosen_splash = champ_alias + "_" + str(skin_number) + ".jpg"

	full_skin_name = None
	champ_description = None
	rarity = None
	with open(GS_FOLDER + 'skins.json', 'rb') as f:
		skin_data = bigjson.load(f)
		champ_data = skin_data[str(full_champ_id)]
		full_skin_name, champ_description = [champ_data["name"], champ_data["description"]]
		rarity = champ_data["rarity"]

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

	msg = "**" + full_skin_name + "** (Piece " + piece_letter(left, top) + ")"
	if rarity == 'kLegendary':
		msg = ":star:  " + msg + "  :star:"
	elif rarity in ['kMythic', 'kUltimate']:
		msg = ":star2:  " + msg + "  :star2:"

	if champ_description is not None:
		msg = msg + "\n_" + champ_description + "_"

	await message.channel.send(msg)

def piece_letter(left, top):
	if top == 0 and left == 0:
		return 'A'
	elif top == 0:
		return 'B'
	elif left == 0:
		return 'C'
	else:
		return 'D'