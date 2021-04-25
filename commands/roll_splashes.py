import os
from globals import *
from random import choice, choices
import discord
import os
import json
import re
from datetime import datetime
from json.decoder import JSONDecodeError
from PIL import Image, ImageOps

### Globals ###
ddragon_baseurl = "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/"

percentages = None
rolls = None
id_to_alias_map = None
splash_harems = None

rarity_colors = {
	"kNoRarity": discord.Colour.from_rgb(255,255,254),
	"kEpic": discord.Colour.from_rgb(4, 199, 248),
	"kLegendary": discord.Colour.from_rgb(227, 48, 52),
	"kUltimate": discord.Colour.from_rgb(226, 145, 20),
	"kMythic": discord.Colour.from_rgb(183, 55, 182)
}

time_format = "%m/%d/%Y, %H:%M"
### End Globals ###


def create_user_data_files():
	if not os.path.exists(USER_INFO_FOLDER):
		os.makedirs(USER_INFO_FOLDER)
	if not os.path.exists(SPLASH_HAREM_FILE):
		with open(SPLASH_HAREM_FILE, "w+") as f:
			print('making harem file')
			json.dump({}, f)
	if not os.path.exists(SPLASH_ROLL_TIMERS_FILE):
		with open(SPLASH_ROLL_TIMERS_FILE, "w+") as f:
			print('making rolls file')
			json.dump({}, f)

# id_with_piece has format <id>[A|B|C|D]
async def force_roll(bot, message, id_with_piece):
	await cmd_splash_roll(bot, message, forced_id=id_with_piece[:-1], forced_piece=id_with_piece[-1].upper())

async def cmd_splash_roll(bot, message, forced_id=None, forced_piece=None):
	if not os.path.exists(CHAMP_SPLASH_FOLDER):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	if not os.path.exists(RS_ID_TO_ALIAS_MAPPINGS_FILE) or not os.path.exists(GS_FOLDER + 'rarity-dist.json'):
		print("RARITY DIST OR CHAMPION SUMMARY DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Champs can't be rolled right now. Please ask an admin to refresh the champ splashes!")
		return

	user_id = str(message.author.id)

	ttr = time_left(user_id)
	if ttr > 0 and not only_for_testing_server(message.guild.id):
		await message.channel.send(f"You can't roll yet! You have {ttr} minutes left!")
		return 

	'''
		1. Pick a random thing out of the rarity-dist
		2. The 3 rightmost numbers are the skin number
		3. All numbers left of that are the champion ID
		4. Use champion-summary.json to get the Alias from ID
		5. Combine <Alias_SkinNumber> to get the jpg
		6. Query skins.json to get full skin name and description
	'''
	if forced_id == None:
		global percentages, rolls 
		if percentages == None or rolls == None:
			with open(GS_FOLDER + 'rarity-dist.json', 'r') as f:
				rarity_dist = json.load(f)
				loot_pools = [(v['percentage'], v['rolls']) for v in rarity_dist.values()]
				percentages, rolls = [list(t) for t in zip(*loot_pools)]

		res_index = choices(range(len(rolls)), weights=percentages)[0]
		chosen_pool = rolls[res_index]

		full_champ_id = choices(chosen_pool)[0]
	else:
		full_champ_id = int(forced_id)

	full_skin_name = None
	champ_description = None
	rarity = None
	with open(SKINS_DATAFILE, 'r') as f:
		skin_data = json.load(f)
		champ_data = skin_data[str(full_champ_id)]
		full_skin_name, champ_description = [champ_data["name"], champ_data["description"]]
		rarity, chosen_splash = [champ_data["rarity"], champ_data["splash_name"]]
	# ------------------------------

	# Pick one of 4 pieces of the splash
	im = Image.open(CHAMP_SPLASH_FOLDER + chosen_splash)
	x, y = im.size

	if forced_piece == None:
		left = choice([0, x / 2])
		top = choice([0, y / 2])

		letter = piece_letter(left, top)
	else:
		letter = forced_piece
	
	# ------------------------------------------------

	# Add to person's list
	global splash_harems
	if splash_harems == None:
		with open(SPLASH_HAREM_FILE, 'r') as f:
			try:
				splash_harems = json.load(f)
			except JSONDecodeError:
				print("Harems file was empty, it never should be")
				splash_harems = {}

	id_string = str(full_champ_id)
	inventory = splash_harems.get(user_id, {})
	if id_string in inventory:
		inventory[id_string]["pieces"][letter] += 1
	else:
		starting_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
		starting_counts[letter] += 1
		inventory[id_string] = {"name": full_skin_name, "pieces": starting_counts}
	splash_harems[user_id] = inventory

	with open(SPLASH_HAREM_FILE, 'w') as f:
		json.dump(splash_harems, f)
	
	# -------------------------------------

	# Create the embed
	pieces_counts = splash_harems[user_id][id_string]["pieces"]
	embed, f = create_progress_embed(full_skin_name, champ_description, rarity, chosen_splash,
	 								pieces_counts, im, bot)
	embed_msg = message.channel.send(embed=embed, file=f)
	os.remove(TEMP_IMAGE_FNAME)
	await embed_msg
	# ----------------------------------

	# Add time to rolls json
	with open(SPLASH_ROLL_TIMERS_FILE, 'r+') as f:
		rolls_info = json.load(f)
		rolls_info[user_id] = datetime.now().strftime(time_format)
		f.seek(0)
		f.truncate()
		json.dump(rolls_info, f)
	# ----------------------


async def cmd_splash_list(bot, message, args):
	if not os.path.exists(SPLASH_HAREM_FILE):
		print("SPLASH HAREMS FILE DOESN'T EXIST, RESTART BOT")
		await message.channel.send("Splash harems aren't available right now, please contact an admin.")
		return
	if not os.path.exists(SKINS_DATAFILE):
		print("SKINS FILE DOESN'T EXIST, RESTART BOT")
		await message.channel.send("Skin info isn't available right now, please contact an admin.")
		return
	
	show_number = False
	user_id = str(message.author.id)
	if len(args) == 1:
		if (args[0] == 'c'):      # show counts
			show_number = True
		else:                     # check for user id
			m = re.match("<@!(\d+)>", args[0])
			if m is not None:
				user_id = m.group(1)
			else:
				await message.channel.send("That user doesn't exist!")
				return

	with open(SPLASH_HAREM_FILE, 'r') as f:
		champs = json.load(f).get(user_id, {})
	if len(champs) == 0:
		await message.channel.send("This harem is empty.")
		return
	else:
		champs_list = []
		for k in sorted(champs, key=int):
			pieces_count = champs[k]["pieces"]
			pieces = []
			for p in sorted(pieces_count):
				count = pieces_count[p]
				if count > 0:
					if show_number:
						pieces.append(p + ' (' + str(count) + ')')
					else:
						pieces.append(p)
			if all(pieces_count.values()) and not show_number:
				champs_list.append('#' + k + ': ' + champs[k]["name"] +
										' (**Complete**)')
			else:
				champs_list.append('#' + k + ': ' + champs[k]["name"] +
										' (Pieces: ' + ', '.join(pieces) + ')')

		# TODO: use cool reactable embed a la Mudae instead
		champs_msg = f'**{message.author.name}\'s champs**\n' + '\n'.join(champs_list)
		await message.channel.send(champs_msg)

# Precondition: len(args) > 0, contains list of divorcees in format <id>[A|B|C|D]
async def divorce_splash(bot, message, args):
	user_id = str(message.author.id)
	with open(SPLASH_HAREM_FILE, 'r+') as f:
		harems = json.load(f)
		user_harem = harems.get(user_id, {})
		if len(user_harem) > 0:
			msgs = []
			for d in args:
				d = d.upper()
				if re.match("\d{4,}[ABCD]", d) is None:
					msgs.append(message.channel.send("Please divorce by valid ID"))
					break
				skin_id, l = d[:-1], d[-1]
				if skin_id in user_harem:
					msgs.append(message.channel.send("Divorced %s!" % (user_harem[skin_id]["name"] + " (Piece " + l + ')')))
					if user_harem[skin_id]["pieces"][l] == 0:
						msgs.append(message.channel.send("You don't own #%s!" % (d)))
					else:
						user_harem[skin_id]["pieces"][l] -= 1
						if not all(user_harem[skin_id]["pieces"].values()):
							del user_harem[skin_id]
				else:
					msgs.append(message.channel.send("You don't own #%s!" % (d)))
					
			harems[user_id] = user_harem
			f.seek(0)
			f.truncate()
			json.dump(harems, f)
			for m in msgs:
				await m
		else:
			await message.channel.send("You have no one to divorce!")
			return

async def info_splash(bot, message, args):
	user_id = str(message.author.id)
	# combine args into single space-separated string
	# do an equals check on everything in skins.json
	# show embed for champion
	m = re.match("\d{4,}", args[0])
	search_by_id = False
	if m is not None:
		skin_id = m.group(0)
		search_by_id = True
	else:
		skin_name = ' '.join(args)

	global splash_harems
	if splash_harems == None:
		with open(SPLASH_HAREM_FILE, 'r') as f:
			splash_harems = json.load(f)
	
	your_harem = splash_harems.get(user_id, None)
	if your_harem is None:
		await message.channel.send("You own nothing")
		return
	
	with open(SKINS_DATAFILE, 'r') as f:
		skins_info = json.load(f)
		
		if search_by_id:
			v = your_harem.get(skin_id, None)
		else:  # Else, search by name
			v = next(filter(lambda s: skin_name.lower() ==
                            s[1]['name'].lower(), your_harem.items()), None)
			skin_id = v[0] if v is not None else None

		if v is None:
			await message.channel.send("You don't have that!")
			return

		this_skin = skins_info[skin_id]
		splash_fname = this_skin["splash_name"]
		skin_id = str(this_skin["id"])

		im = Image.open(CHAMP_SPLASH_FOLDER + splash_fname)
		pieces_counts = your_harem[skin_id]["pieces"]

		embed, f = create_progress_embed(this_skin["name"], this_skin["description"], this_skin["rarity"], splash_fname,
										pieces_counts, im, bot)
		
		embed_msg = message.channel.send(embed=embed, file=f)
		os.remove(TEMP_IMAGE_FNAME)
		await embed_msg

# Creates an embed with a progress picture given an image and piece counts
def create_progress_embed(skin_name, description, rarity, splash_fname, pieces_counts, im, bot):
	cropped_img = get_progress_img(pieces_counts, im, rarity)
	cropped_img.save(TEMP_IMAGE_FNAME, "jpeg")

	title = decorated_title("**" + skin_name + "**", rarity, bot)
	desc = ""
	if description is not None:
		desc = "_" + description + "_"

	embed = discord.Embed(title=title, url=ddragon_baseurl + splash_fname,
					description=desc, color=rarity_colors[rarity]) \
				.set_image(url="attachment://" + TEMP_IMAGE_FNAME)
	f = (discord.File(TEMP_IMAGE_FNAME))
	return (embed, f)


# Return letter corresponding to cropped corner
def piece_letter(left, top):
	if top == 0 and left == 0:
		return 'A'
	elif top == 0:
		return 'B'
	elif left == 0:
		return 'C'
	else:
		return 'D'

# Inverse of piece_letter
def coordinates(letter, x, y):
	if letter == 'A':
		return (0, 0, x // 2, y // 2)
	elif letter == 'B':
		return (x // 2, 0, x, y // 2)
	elif letter == 'C':
		return (0, y // 2, x // 2, y)
	elif letter == 'D':
		return (x // 2, y // 2, x, y)

def decorated_title(title, rarity, bot):
	if rarity == 'kLegendary':
		l_id = bot.rarity_emoji_ids['legendary']
		title = f"<:legendary:{l_id}> " + title + f"  <:legendary:{l_id}>"
	elif rarity == 'kMythic':
		m_id = bot.rarity_emoji_ids['mythic']
		title = f"<:mythic:{m_id}>  " + title + f"  <:mythic:{m_id}>"
	elif rarity == 'kEpic':
		e_id = bot.rarity_emoji_ids['epic']
		title = f"<:epic:{e_id}>  " + title + f"  <:epic:{e_id}>"
	elif rarity == 'kUltimate':
		u_id = bot.rarity_emoji_ids['ultimate']
		title = f"<:ultimate:{u_id}>  " + title + f"  <:ultimate:{u_id}>"
	return title


# show pieces the user has over a gray overlay 
def get_progress_img(pieces_counts, image_file: Image, rarity) -> Image:
	letters = ['A', 'B', 'C', 'D']

	not_owned = list(filter(lambda l: pieces_counts[l] == 0, letters))

	x, y = image_file.size

	for l in not_owned:
		image_file.paste("#808080", coordinates(l, x, y))
	if len(not_owned) == 0:
		fill = '#' + hex(rarity_colors[rarity].value).replace('0x', '').zfill(6)
		image_file = add_padding(image_file, 5, fill)

	return image_file

def add_padding(image_file: Image, p=5, fill='black') -> Image:
	x, y = image_file.size
	return ImageOps.expand(image_file.crop((p, p, x-p, y-p)), border=5, fill=fill)

def time_left(user_id: str) -> int:
	with open(SPLASH_ROLL_TIMERS_FILE, 'r') as f:
		rolls_info = json.load(f)
		if user_id in rolls_info:
			earlier_roll_str = rolls_info[user_id]
			earlier_roll = datetime.strptime(earlier_roll_str, time_format)
			hour_diff = (datetime.now() - earlier_roll).seconds / 3600

			if hour_diff >= 1:
				return 0
			else:
				return int(60 - (hour_diff * 60))
		else:  # they've never rolled before
			return 0
