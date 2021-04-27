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

from Franklin import *

### Globals ###
ddragon_baseurl = "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/"

percentages = None
rolls = None
id_to_alias_map = None
splash_harems = None

rarity_colors = {
	"kNoRarity": discord.Colour.from_rgb(255,255,254),
	"kRare": discord.Colour.from_rgb(255, 255, 254),
	"kEpic": discord.Colour.from_rgb(4, 199, 248),
	"kLegendary": discord.Colour.from_rgb(227, 48, 52),
	"kUltimate": discord.Colour.from_rgb(226, 145, 20),
	"kMythic": discord.Colour.from_rgb(183, 55, 182)
}

time_format = "%m/%d/%Y, %H:%M"
skin_id_regex = "\d{4,}[ABCD]"
attachment_prefix = "attachment://"

champs_per_page = 10
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
	if not os.path.exists(SPLASH_LINK_MAPPINGS_FILE):
		with open(SPLASH_LINK_MAPPINGS_FILE, "w+") as f:
			print('making link mappings file')
			json.dump({}, f)

# id_with_piece has format <id>[A|B|C|D]
async def force_roll(bot, message, id_with_piece):
	await cmd_splash_roll(bot, message, forced_id=id_with_piece[:-1], forced_piece=id_with_piece[-1].upper())

async def cmd_splash_roll(bot, message, forced_id=None, forced_piece=None):
	if not os.path.exists(CHAMP_SPLASH_FOLDER):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	if not os.path.exists(RS_ID_TO_ALIAS_MAPPINGS_FILE) or not os.path.exists(RARITY_DIST_FILE):
		print("RARITY DIST OR CHAMPION SUMMARY DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Champs can't be rolled right now. Please ask an admin to refresh the champ splashes!")
		return

	user_id = str(message.author.id)

	ttr = time_left(user_id)
	if ttr > 0: # and not only_for_testing_server(message.guild.id):
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
			with open(RARITY_DIST_FILE, 'r') as f:
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
	im = Image.open(os.path.join(CHAMP_SPLASH_FOLDER, chosen_splash))
	x, y = im.size

	if forced_piece == None:
		left = choice([0, x / 2])
		top = choice([0, y / 2])

		letter = piece_letter(left, top)
	else:
		letter = forced_piece
	
	im.crop(coordinates(letter, x, y)).save(CROPPED_IMAGE_FNAME, "jpeg")
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
		inventory[id_string] = get_starting_pieces(full_skin_name, letter)
	splash_harems[user_id] = inventory

	with open(SPLASH_HAREM_FILE, 'w') as f:
		json.dump(splash_harems, f)
	
	# -------------------------------------

	# Create the embed
	skin_name = f"{full_skin_name} (Piece {letter})"
	title = decorated_title("**" + skin_name + "**", rarity, bot)
	desc = ""
	if champ_description is not None:
		desc = "_" + champ_description + "_"

	embed = discord.Embed(title=title, description=desc,
                       color=rarity_colors[rarity], url=ddragon_baseurl + chosen_splash) \
              			.set_image(url=attachment_prefix + CROPPED_IMAGE_FNAME)

	f = (discord.File(CROPPED_IMAGE_FNAME))

	await message.channel.send(embed=embed, file=f)
	os.remove(CROPPED_IMAGE_FNAME)
	# ----------------------------------

	# Add time to rolls json
	with open(SPLASH_ROLL_TIMERS_FILE, 'r+') as f:
		rolls_info = json.load(f)
		if user_id in rolls_info:
			if rolls_info[user_id]["rolls_left"] == 0:
				rolls_info[user_id] = {"rolls_left": 3, "start": datetime.now().strftime(time_format)}
			else:
				rolls_info[user_id]["rolls_left"] -= 1
		else:
			rolls_info[user_id] = {"rolls_left": 3, "start": datetime.now().strftime(time_format)}
		f.seek(0)
		f.truncate()
		json.dump(rolls_info, f)
	# ----------------------


async def cmd_splash_list(bot, message, args, client):
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
	harem_owner = message.author.name
	if len(args) == 1:
		if (args[0] == 'c'):      # show counts
			show_number = True
		else:                     # check for user id
			m = re.match("<@!(\d+)>", args[0])
			if m is not None:
				user_id = m.group(1)
				harem_owner = client.get_user(int(user_id))
				if harem_owner is None:
					harem_owner = await client.fetch_user(int(user_id))
					if harem_owner is None:
						await message.channel.send("user doesn't exist i guess")
						return
				harem_owner = harem_owner.name
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
				champs_list.append('#**' + k + '**: ' + champs[k]["name"] +
										' (**Complete**)')
			else:
				champs_list.append('#**' + k + '**: ' + champs[k]["name"] +
										' (Pieces: ' + ', '.join(pieces) + ')')

		# TODO: use cool reactable embed a la Mudae instead
		# Constants
		chunks = [champs_list[i:i + champs_per_page] for i in range(0, len(champs_list), champs_per_page)]
		champs_desc = '\n'.join(champs_list[:champs_per_page])
			
		embed = discord.Embed(title=f"{harem_owner}\'s champs", 
		                      description=champs_desc) \
                    .set_footer(text=f"Page 1 / {len(chunks)}")
		msg = await message.channel.send(embed=embed)
		await msg.add_reaction("⬅️")
		await msg.add_reaction("➡️")

		reactions = ["⬅️", "➡️"]
		functions = [scroll] * 2
		Franklin(bot, msg, reactions, functions,{"chunks": chunks, "index": 0})

async def scroll(data, _, embed_msg, reaction):
	chunks = data["chunks"]
	if reaction == "➡️":
		if data["index"] >= len(chunks) - 1:
			data["index"] = 0
		else:
			data["index"] += 1
	elif reaction == "⬅️":
		if data["index"] == 0:
			data["index"] = len(chunks) - 1
		else:
			data["index"] -= 1
	
	new_chunk = chunks[data["index"]]
	embed = embed_msg.embeds[0]
	embed.description = '\n'.join(new_chunk)
	embed.set_footer(text=f"Page {data['index'] + 1} / {len(chunks)}")
	await embed_msg.edit(embed=embed)


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
				if re.match(skin_id_regex, d) is None:
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

		im = Image.open(os.path.join(CHAMP_SPLASH_FOLDER, splash_fname))
		im.save(FULL_IMAGE_FNAME, "jpeg")
		pieces_counts = your_harem[skin_id]["pieces"]

		embed, f = create_progress_embed(this_skin["name"], this_skin["description"], this_skin["rarity"], splash_fname,
										pieces_counts, im, bot)
		

		embed.set_image(
			url=attachment_prefix + CROPPED_IMAGE_FNAME)
		msg = await message.channel.send(embed=embed, file=f)

		os.remove(FULL_IMAGE_FNAME)
		os.remove(CROPPED_IMAGE_FNAME)


async def trade_splashes(bot, message, args):
	user_id = str(message.author.id)
	# Figure out if we're initiating or responding to a trade
	if len(args) == 3:
		# initiate trade
		m = re.match("<@!(\d+)>", args[0])
		if m is None:
			print(args[0], 'this is the mention that broke')
			await message.channel.send("Must @ who you want to trade with")
			return
		
		tradee_id = m.group(1)
		if bot.active_trades.get(tradee_id, None) is not None:
			await message.channel.send("Active trade in progress with that user already! Try again later.")
			return
		
		# m1 and m2 are of form <id[ABCD]>
		args = list(map(lambda x: x.upper(), args))
		m1 = re.match(skin_id_regex, args[1])
		m2 = re.match(skin_id_regex, args[2])
		if m1 is None or m2 is None:
			await message.channel.send("Must be valid skin IDs")
			return
		bot.active_trades[tradee_id] = {"trader_id": user_id, 
										"trader_offer": args[1], 
										"tradee_offer": args[2]}


		with open(SKINS_DATAFILE, 'r') as f:
			skins_data = json.load(f)
		
		trader_offer = skins_data[args[1][:-1]]['name']
		trader_piece = args[1][-1]
		tradee_offer = skins_data[args[2][:-1]]['name']
		tradee_piece = args[2][-1]

		await message.channel.send((f"<@{tradee_id}>, {trader_offer} (Piece {trader_piece}) is being"
									f" offered to you in exchange for {tradee_offer} (Piece {tradee_piece})."
									" Use `[$ts|$trade_splash] [y|yes|n|no]` to respond."))
	elif len(args) == 1:
		# respond
		trade = bot.active_trades.get(user_id, None)
		if trade is None:
			await message.channel.send("No one is trading with you right now!")
			return

		response = args[0]

		if response in ['y', 'yes']:
			with open(SPLASH_HAREM_FILE, 'r+') as f:
				harems = json.load(f)
				trader_skin_id, trader_piece = [trade["trader_offer"][:-1], trade["trader_offer"][-1]]
				their_offer = harems.get(trade["trader_id"], {}).get(trader_skin_id, {}).get("pieces", {}).get(trader_piece)
				if their_offer == 0 or their_offer is None:
					await message.channel.send("Trader doesn't have their offer, please no bamboozle >:(. Cancelling trade.")
					del bot.active_trades[user_id]
					return

				tradee_skin_id, tradee_piece = [trade["tradee_offer"][:-1], trade["tradee_offer"][-1]]
				your_offer = harems.get(user_id, {}).get(tradee_skin_id, {}).get("pieces", {}).get(tradee_piece)
				if your_offer == 0 or your_offer is None:
					await message.channel.send("YOU don't have your offer, bamboozling is strictly prohibited. Trade cancelled.")
					del bot.active_trades[user_id]
					return
				
				# Both people have their offers, commence trade
				# Remove pieces
				your_harem, their_harem = [harems[user_id], harems[trade["trader_id"]]]
				your_harem[tradee_skin_id]["pieces"][tradee_piece] -= 1
				their_harem[trader_skin_id]["pieces"][trader_piece] -= 1

				with open(SKINS_DATAFILE, 'r') as f2:
					skins_data = json.load(f2)
					trader_skin_name = skins_data[trader_skin_id]["name"]
					tradee_skin_name = skins_data[tradee_skin_id]["name"]

				# Add pieces
				if tradee_skin_id in their_harem:
					their_harem[tradee_skin_id]["pieces"][tradee_piece] += 1
				else:
					their_harem[tradee_skin_id] = get_starting_pieces(tradee_skin_name, tradee_piece)
				
				if trader_skin_id in your_harem:
					your_harem[trader_skin_id]["pieces"][trader_piece] += 1
				else:
					your_harem[trader_skin_id] = get_starting_pieces(trader_skin_name, trader_piece)

				# If any skin piece counts ended up empty, delete.
				if not all(your_harem[tradee_skin_id]["pieces"].values()):
					del your_harem[tradee_skin_id]
				if not all(their_harem[trader_skin_id]["pieces"].values()):
					del their_harem[trader_skin_id]
				
				await message.channel.send("Trade successful!")

				harems[user_id] = your_harem
				harems[trade["trader_id"]] = their_harem

				f.seek(0)
				f.truncate()
				json.dump(harems, f)

		elif response in ['n', 'no']:
			await message.channel.send("Trade declined.")
			del bot.active_trades[user_id]
		else: 
			await message.channel.send("Invalid response.")

	else:
		await message.channel.send("Incorrect usage of trade command")

async def punish(bot, message, args):
	m = re.match("<@!(\d+)>", args[0])
	if m is None:
		await message.channel.send("Please @ whoever you want to punish.")
		return
	punished_id = m.group(1)

	with open(SPLASH_HAREM_FILE, 'r+') as f:
		harems = json.load(f)
		if punished_id in harems:
			del harems[punished_id]
		
		f.seek(0)
		f.truncate()
		json.dump(harems, f)

	await message.channel.send("Punishment has been dealt.")


# --------------------  END MAIN METHODS     ----------------------- #
# --------------------  HELPER METHODS BELOW ----------------------- #

# Creates an embed with a progress picture given an image and piece counts
def create_progress_embed(skin_name, description, rarity, splash_fname, pieces_counts, im, bot):
	cropped_img = get_progress_img(pieces_counts, im, rarity)
	cropped_img.save(CROPPED_IMAGE_FNAME, "jpeg")

	title = decorated_title("**" + skin_name + "**", rarity, bot)
	desc = ""
	if description is not None:
		desc = "_" + description + "_"

	embed = discord.Embed(title=title, url=ddragon_baseurl + splash_fname,
					description=desc, color=rarity_colors[rarity]) \
					.set_image(url=attachment_prefix + CROPPED_IMAGE_FNAME)
	f = (discord.File(CROPPED_IMAGE_FNAME))
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
	if title == "**Frostblade Irelia (Piece D)**":
		u_id = bot.rarity_emoji_ids['ultimate']
		title = f"<:ultimate:{u_id}> **Frostbutt Irelia (Piece D)** <:ultimate:{u_id}>"
		# NONE OF YOU FUCKERS BETTER SPOIL THIS
	elif rarity == 'kUltimate':
		u_id = bot.rarity_emoji_ids['ultimate']
		title = f"<:ultimate:{u_id}>  {title}  <:ultimate:{u_id}>"
	elif rarity == 'kMythic':
		m_id = bot.rarity_emoji_ids['mythic']
		title = f"<:mythic:{m_id}>  {title}  <:mythic:{m_id}>"
	elif rarity == 'kLegendary':
		l_id = bot.rarity_emoji_ids['legendary']
		title = f"<:legendary:{l_id}> {title} <:legendary:{l_id}>"
	elif rarity == 'kEpic':
		e_id = bot.rarity_emoji_ids['epic']
		title = f"<:epic:{e_id}>  {title}  <:epic:{e_id}>"
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

# TODO: change this to 3 times every 3 hours
def time_left(user_id: str) -> int:
	with open(SPLASH_ROLL_TIMERS_FILE, 'r') as f:
		rolls_info = json.load(f)
		if user_id in rolls_info:
			if rolls_info[user_id]["rolls_left"] == 0:
				earlier_roll_str = rolls_info[user_id]["start"]
				earlier_roll = datetime.strptime(earlier_roll_str, time_format)
				hour_diff = (datetime.now() - earlier_roll).seconds / 3600
				return int(60 * 3 - (hour_diff * 60))
			else:
				return 0
		else:  # they've never rolled before
			return 0

def get_starting_pieces(skin_name, starting_letter):
	starting_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
	starting_counts[starting_letter] += 1
	return {"name": skin_name, "pieces": starting_counts}
