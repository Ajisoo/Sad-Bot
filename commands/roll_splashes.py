import os
from globals import *
from random import randrange, choice, choices
import discord
import os
import json
from datetime import datetime
from json.decoder import JSONDecodeError
from PIL import Image, ImageOps

### Globals ###

latest_version = None

champ_splashes_folder = GS_FOLDER + "img" + os.path.sep + "champion" + os.path.sep + "splash" + os.path.sep
champ_loadingsplash_folder = GS_FOLDER + "img" + os.path.sep + "champion" + os.path.sep + "loading" + os.path.sep
skins_file = GS_FOLDER + 'skins.json'

ddragon_baseurl = "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/"

temp_image_name = "tempCroppedSplash.jpg"

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
	if not os.path.exists(SPLASH_HAREM_FILE):
		if not os.path.exists(USER_INFO_FOLDER):
			os.makedirs(USER_INFO_FOLDER)
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
	if not os.path.exists(champ_loadingsplash_folder):
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

		res_index = choices(range(len(rolls)), weights=[100 * p for p in percentages])[0]
		chosen_pool = rolls[res_index]

		full_champ_id = choices(chosen_pool)[0]
	else:
		full_champ_id = int(forced_id)

	full_skin_name = None
	champ_description = None
	rarity = None
	with open(skins_file, 'r') as f:
		skin_data = json.load(f)
		champ_data = skin_data[str(full_champ_id)]
		full_skin_name, champ_description = [champ_data["name"], champ_data["description"]]
		rarity, chosen_splash = [champ_data["rarity"], champ_data["splash_name"]]
	# ------------------------------

	# Pick one of 4 pieces of the splash
	im = Image.open(champ_loadingsplash_folder + chosen_splash)
	x, y = im.size

	if forced_piece == None:
		left = choice([0, x / 2])
		right = left + x / 2
		top = choice([0, y / 2])
		bottom = top + y / 2

		letter = piece_letter(left, top)
		crop_coords = (left, top, right, bottom)
	else:
		letter = forced_piece
		crop_coords = coordinates(forced_piece, x, y)

	cropped_img = im.crop(crop_coords)
	
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

	splash_piece = str(full_champ_id) + letter
	inventory = splash_harems.get(user_id, {})
	inventory[splash_piece] = full_skin_name
	splash_harems[user_id] = inventory

	with open(SPLASH_HAREM_FILE, 'w') as f:
		json.dump(splash_harems, f)
	
	cropped_img = get_progress_img(splash_harems, user_id, full_champ_id, im, rarity)
	cropped_img.save(temp_image_name, "jpeg")
	# -------------------------------------

	# Decorate the embed 
	title = "**" + full_skin_name + "** (Piece " + letter + ")"
	title = decorated_title(title, rarity, bot)
	
	desc = ""
	if champ_description is not None:
		desc = "_" + champ_description + "_"
	
	embed = discord.Embed(title=title, url=ddragon_baseurl + chosen_splash, 
						  description=desc, color=rarity_colors[rarity]) \
							.set_image(url="attachment://" + temp_image_name)
	f = (discord.File(temp_image_name))
	embed_msg = message.channel.send(embed=embed, file=f)
	os.remove(temp_image_name)
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
	if not os.path.exists(skins_file):
		print("SKINS FILE DOESN'T EXIST, RESTART BOT")
		await message.channel.send("Skin info isn't available right now, please contact an admin.")
		return
	
	user_id = str(message.author.id)

	champs = {}
	with open(SPLASH_HAREM_FILE, 'r') as f:
		champs = json.load(f).get(user_id, {})
	if len(champs) == 0:
		await message.channel.send("You have nothing.")
		return
	else:
		with open(skins_file, 'r') as f:
			skin_data = json.load(f)
			champs_dict = {}
			for k in champs.keys():
				a, b = k[:-1], k[-1]
				if a in champs_dict:
					champs_dict[a].append(b)
				else:
					champs_dict[a] = [b]
			champs_list = []
			for k in sorted(champs_dict, key=int):
				pieces = sorted(champs_dict[k])
				if len(pieces) == 4:
					champs_list.append('#' + k + ': ' + skin_data[k]['name'] +
                                            ' (**Complete**)')
				else:
					champs_list.append('#' + k + ': ' + skin_data[k]['name'] +
                                            ' (Pieces: ' + ', '.join(pieces) + ')')

		# TODO: use cool reactable embed a la Mudae instead
		champs_msg = f'**{message.author.name}\'s champs**\n' + '\n'.join(champs_list)
		await message.channel.send(champs_msg)

# Precondition: len(args) > 0, contains list of divorcees in format <id>[A|B|C|D]
async def divorce_splash(bot, message, args):
	with open(SPLASH_HAREM_FILE, 'r+') as f:
		harems = json.load(f)
		user_harem = harems.get(str(message.author.id), {})
		if len(user_harem) > 0:
			msgs = []
			for d in args:
				d = d.upper()
				if d in user_harem:
					msgs.append(message.channel.send("Divorced %s!" % (user_harem[d] + " (Piece " + d[-1] + ')')))
					del user_harem[d]
				else:
					msgs.append(message.channel.send("You don't own %s!" % (d)))
			harems[message.author.id] = user_harem
			f.seek(0)
			f.truncate()
			json.dump(harems, f)
			for m in msgs:
				await m
		else:
			await message.channel.send("You have no one to divorce!")
			return

async def info_splash(bot, message, args):
	# combine args into single space-separated string
	# do an equals check on everything in skins.json
	# show embed for champion
	skin_name = ' '.join(args)

	full_skin_name = None
	champ_description = None
	rarity = None
	splash_fname = None
	with open(skins_file, 'r') as f:
		skins_info = json.load(f)
		for v in skins_info.values():
			if skin_name.lower() == v['name'].lower():
				# this is mostly copied from splash_roll code, minus the cropping stuff
				# TODO: refactor this into a function or something
				full_skin_name, champ_description, rarity, splash_fname = [v["name"], v["description"], v["rarity"], v["splash_name"]]
				title = decorated_title("**" + full_skin_name + "**", rarity, bot)
				desc = ""
				if champ_description is not None:
					desc = "_" + champ_description + "_"
				im = Image.open(champ_loadingsplash_folder + splash_fname)
				im.save(temp_image_name, "jpeg")
				embed = discord.Embed(title=title, url=ddragon_baseurl + splash_fname,
                                    description=desc, color=rarity_colors[rarity]) \
                                    .set_image(url="attachment://" + temp_image_name)
				f = (discord.File(temp_image_name))
				embed_msg = message.channel.send(embed=embed, file=f)
				os.remove(temp_image_name)
				await embed_msg
				return

	await message.channel.send(f"{skin_name} is not a champion!")

	


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
def get_progress_img(harems_data, user_id, skin_id, image_file: Image, rarity) -> Image:
	letters = ['A', 'B', 'C', 'D']

	not_owned = list(filter(lambda l: str(skin_id) + l not in harems_data[user_id], letters))

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

