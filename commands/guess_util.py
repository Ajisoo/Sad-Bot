import json
import random
from random import randrange
import re
import os
import shutil

from bs4 import BeautifulSoup
import discord
import ffmpeg
from PIL import Image
import requests

import commands.leaderboard_util
from globals import *
from commands.roll_splashes import coordinates

async def cmd_ga_refresh(bot, message, _args):
	if message.author.id not in ADMINS:  # Us
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

		with open(os.path.join(GA_FOLDER, f"{counter}img.png"), "wb+") as image_file:
			image_file.write(requests.get(GA_BASE_WEBSITE + image).content)

		with open(os.path.join(GA_FOLDER, f"{counter}info.txt"), "w+") as text_file:
			text_file.write(ability_name + "\n" + champ_name + "\n" + ability_key)

		counter += 1

	with open(os.path.join(GA_FOLDER, "!len.txt"), "w+") as length_file:
		length_file.write(str(counter))

	bot.g_valid = True
	await message.channel.send("All done")

GUESS_UNSTARTED_PROMPT = f"There's nothing to guess! Start with {BOT_PREFIX}guess_ability, guess_splash, or guess_undertale"

async def cmd_guess(bot, message, args):
	if len(bot.g_answer) == 0:
		await message.channel.send(GUESS_UNSTARTED_PROMPT)
		return

	# Ignore basic semotes
	args = list(filter(lambda x: not (x.startswith(":") and x.endswith(":")), args))

	guess_arg = re.sub(r'[^a-z0-9]', '', " ".join(args).lower())
	if bot.g_answer == guess_arg:
		bot.g_answer_raw = ""
		bot.g_answer = ""
		await message.channel.send(f"<@{message.author.id}> is Correct!")

		commands.leaderboard_util.update_leaderboards_file(message.author.id, bot.guess_type)


async def cmd_give_up(bot, message, _args):
	if len(bot.g_answer) == 0:
		await message.channel.send(GUESS_UNSTARTED_PROMPT)
		return
	await message.channel.send("Answer was: " + bot.g_answer_raw)
	bot.g_answer_raw = ""
	bot.g_answer = ""
	# Uncomment these if giving up should stop the current song
	# vc = message.guild.voice_client
	# if vc:
	# 	vc.stop()

async def cmd_ga_start(bot, message, args):
	if not bot.g_valid:
		return
	len_file = open(os.path.join(GA_FOLDER, "!len.txt"), "r")
	rand = randrange(int(len_file.readline()))
	len_file.close()
	info_file = open(os.path.join(GA_FOLDER, f"{rand}info.txt"), "r")
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
	await message.channel.send(file=(discord.File(os.path.join(GA_FOLDER, f"{rand}img.png"))))


# ----------------------------------------------------------------------------------------------


#### SPLASH CONSTANTS #####

latest_version = None

versions_endpoint = 'https://ddragon.leagueoflegends.com/api/versions.json'
data_dragon_endpoint_base = 'https://ddragon.leagueoflegends.com/cdn/dragontail-'
cdragon_skins_url = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json'
cdragon_champsummaries_url = 'http://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json'

dumpfile_name = os.path.join(GS_FOLDER, 'dump.tgz')
latest_version_file = os.path.join(GS_FOLDER, "latest_version.txt")





### SPLASH CONSTANTS END ###

async def cmd_gs_refresh(bot, message, _args):
	if message.author.id not in ADMINS:  # Us
		return
	
	# Get the latest patch number
	response = requests.get(versions_endpoint)
	
	# Create the data directory if not exists
	if not os.path.exists(GS_FOLDER):
		os.makedirs(GS_FOLDER)

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
			return
		
	except Exception as e:
		print(f"Getting latest version has failed: {e}")

	bot.g_valid = False


	# Get the data dragon dump
	data_dragon_endpoint_full = data_dragon_endpoint_base + latest_version + ".tgz"
	print(data_dragon_endpoint_full)

	await message.channel.send("Loading champ splashes...")

	await GET_remote_file(data_dragon_endpoint_full, dumpfile_name, message)

	# GET tasks
	get_skins = GET_remote_file(cdragon_skins_url, SKINS_DATAFILE, message)
	get_aliases = GET_remote_file(cdragon_champsummaries_url,
	                RS_ID_TO_ALIAS_MAPPINGS_FILE, message)

	await message.channel.send("Unpacking data...")
	print("Unpacking data dump...")
	shutil.unpack_archive(dumpfile_name, GS_FOLDER)
	print("Done unpacking data dump!")

	for fname in os.listdir(TENTH_ANNIVERSARY_SKINS_FOLDER):
		shutil.copy2(os.path.join(TENTH_ANNIVERSARY_SKINS_FOLDER, fname), CHAMP_SPLASH_FOLDER)

	# Get skins json (which has rarity info)
	await get_skins

	# Turn skins json into smaller version of itself
	await message.channel.send("Getting skin data...")
	global RARITY_DIST
	new_skin_data = {}
	with open(SKINS_DATAFILE, "r") as f, \
		open(TENTH_ANNIVERSARY_SKINS_JSON, 'r') as f2:
		skin_data = json.load(f)
		tenth_skins_data = json.load(f2)
		skin_data.update(tenth_skins_data)
		for k in RARITY_DIST.keys():
			RARITY_DIST[k]['rolls'] = []
		for k, v in skin_data.items():
			if v['rarity'] == 'kRare':
				# kRare only has Conqueror Nautilus and Alistar, just put them with not rare
				RARITY_DIST['kNoRarity']['rolls'].append(v['id'])
			else:
				RARITY_DIST[v['rarity']]['rolls'].append(v['id'])
			new_skin_data[k] = {key: v[key]
                            for key in ['id', 'name', 'description', 'rarity']}
	with open(RARITY_DIST_FILE, "w", encoding='utf-8') as f:
		json.dump(RARITY_DIST, f)


	# Get champion summaries (which has ID to champ alias mappings)
	await get_aliases

	# Turn champ summaries into a (name:id) mapping json
	await message.channel.send("Creating some mappings, almost done...")
	print("Creating some mappings")
	with open(RS_ID_TO_ALIAS_MAPPINGS_FILE, "r+", encoding="utf-8") as f:
		summary_data = json.load(f)
		
		aliases = {str(summary_data[i]['id']):summary_data[i]['alias']
                    for i in range(len(summary_data))}
		del aliases['-1']  # Delete random placeholder

		# Add image names to skins.json
		# After this point we won't really need champion-summaries.json anymore
		# because the mappings are all consolidated in one file
		for k,v in new_skin_data.items():
			alias = aliases[k[:-3]]
			skin_number = str(int(k[-3:]))
			new_skin_data[k]['splash_name'] = alias + "_" + skin_number + ".jpg"
			if new_skin_data[k]['description'] is not None:
				new_skin_data[k]['description'] = new_skin_data[k]['description'].replace('<br>', '\n').replace('\\n', '\n')

		f.seek(0)
		f.truncate()
		json.dump(aliases, f)
	
	with open(RS_SKIN_NAME_TO_ID_MAPPINGS_FILE, 'w+') as f:
		mappings = {v['name'].lower(): str(v['id']) for v in new_skin_data.values()}
		json.dump(mappings, f)

	with open(SKINS_DATAFILE, "w", encoding='utf-8') as f:
		json.dump(new_skin_data, f, ensure_ascii=False)
	print("Finished with mappings")

	print("Done, champ splashes are ready now!")
	await message.channel.send("Champ splashes are ready now!")

	bot.g_valid = True 


async def cmd_gs_start(bot, message, _args):
	if not os.path.exists(CHAMP_SPLASH_FOLDER):
		print("CHAMP SPLASHES FOLDER DOESN'T EXIST, PLEASE REFRESH")
		await message.channel.send("Please ask an admin to refresh the champ splashes!")
		return
	
	chosen_splash = random.choice(os.listdir(CHAMP_SPLASH_FOLDER))

	# First get the champ + skin number (i.e. Aatrox_2 or Kaisa_3)
	# Then we match this against the data JSON to find the actual skin name

	champ_plus_skin_number = chosen_splash[:chosen_splash.find(".jpg")]

	champ_name, skin_number = champ_plus_skin_number.split("_")
	print(champ_name)
	print(skin_number)

	global latest_version
	if latest_version is None:
		try:
			with open(latest_version_file, "r") as f:
				latest_version = f.readline().strip()
		except Exception as _e:
			print("Latest version file doesn't exist, please refresh")
			await message.channel.send("Latest version file doesn't exist, please refresh")
			return

	# Load the data JSON into memory 
	champ_data_folder = os.path.join(GS_FOLDER, latest_version, "data", "en_US")
	if not os.path.exists(champ_data_folder):
		await message.channel.send("Champ data folder doesn't exist, ask admin to refresh")
		return

	json_data = None
	with open(os.path.join(champ_data_folder, "champion", f"{champ_name}.json"), "r", encoding="utf-8") as f:
		json_data = json.load(f)

	''' If you're wondering why we don't just use the skin number
	    as the index for this array, that's a good question. For some reason
		they're not sequentially numbered like I checked and 16 came after 12
		for some reason. So we go through the whole array. It's roughly O(1) anyways.
	'''
	skins_array = json_data["data"][champ_name]["skins"]
	for skin in skins_array:
		if skin["num"] == int(skin_number):
			print(skin["name"])

			if skin["name"] == "default":
				bot.g_answer_raw = champ_name
			else:
				bot.g_answer_raw = skin["name"]
			
			bot.g_answer = re.sub(r'[^a-z0-9]', '', bot.g_answer_raw.lower())
			break

	im = Image.open(os.path.join(CHAMP_SPLASH_FOLDER, chosen_splash))
	x, y = im.size
	
	left = random.randint(0, x / 2)
	right = left + x / 2
	top = random.randint(0, y - (x / 2))
	bottom = top + x / 2

	cropped_img = im.crop((left, top, right, bottom))

	cropped_img.save(CROPPED_IMAGE_FNAME, "jpeg")
	await message.channel.send(file=(discord.File(CROPPED_IMAGE_FNAME)))
	os.remove(CROPPED_IMAGE_FNAME)

	bot.guess_type = GS_LEADERBOARD_ID
	await message.channel.send("Guess the champion skin!")


async def debug_get_cdragon_json(_bot, _message, args):
	print(args[0])

# Try to get a big file from <url> and save as <fname>
# <message> is used in case of error
async def GET_remote_file(url, fname, message):
	try:
		with requests.get(url, stream=True) as r:
			r.raise_for_status()
			with open(fname, 'w+b') as f:
				for chunk in r.iter_content(chunk_size=10000):
					f.write(chunk)
	except Exception as e:
		print(e)
		await message.channel.send("Error getting info from " + url)
# ----------------------------------------------------------------------------------------------

UT_OST_FOLDER = os.path.join(GUM_FOLDER, "ost")
# Every file starts with this - we could rename them but we're (I'm) lazy
UT_PREFIX_LEN = len("toby fox - UNDERTALE Soundtrack - ")

async def _umq_try_join_vc(_bot, message):
	"""Returns a voice channel if it can connect; otherwise sends a warning and returns"""
	if not os.path.exists(UT_OST_FOLDER):
		print("UNDERTALE OST FOLDER DOESN'T EXIST")
		await message.channel.send("Please ask an admin to fix the undertale OST files!")
		return None
	try:
		voice = message.author.voice
		if not voice:
			await message.channel.send("You must be in a voice channel to start the quiz!")
			return None
		vc = await voice.channel.connect()
	except Exception:
		vc = message.guild.voice_client
	return vc

async def cmd_umq_start(bot, message, _args):
	chosen_song_fn = random.choice(os.listdir(UT_OST_FOLDER))
	vc = await _umq_try_join_vc(bot, message)
	if not vc:
		return
	vc.stop()
	song_path = os.path.join(UT_OST_FOLDER, chosen_song_fn)
	# The starting point is at least 15 seconds away before the end of the song
	duration = int(float(ffmpeg.probe(song_path)['format']['duration']))
	ts_secs = random.randint(0, max(0, duration - 15))
	ts_mm = ts_secs // 60
	ts_ss = ts_secs % 60
	ts = "00:{:02d}:{:02d}".format(ts_mm, ts_ss)

	vc.play(discord.FFmpegPCMAudio(
		executable="./ffmpeg.exe",
		source=song_path,
		options="-ss " + ts
	))
	bot.guess_type = GUM_LEADERBOARD_ID
	# Trim mp3 suffix and album prefix
	bot.g_answer_raw = chosen_song_fn[UT_PREFIX_LEN:-4]
	# First token is always a track number
	song_name = bot.g_answer_raw[bot.g_answer_raw.index(" "):] 
	bot.g_answer = re.sub(r'[^a-z0-9]', '', song_name.lower())
	bot.umq_last_song_fn = chosen_song_fn
	bot.umq_last_song_ts = ts
	print(bot.g_answer + " @ " + ts)
	await message.channel.send("Guess the Undertale song!")

async def cmd_umq_replay(bot, message, _args):
	vc = await _umq_try_join_vc(bot, message)
	if not vc:
		return
	vc.stop()
	chosen_song_fn = bot.umq_last_song_fn
	song_path = os.path.join(UT_OST_FOLDER, chosen_song_fn)
	if chosen_song_fn:
		vc.play(discord.FFmpegPCMAudio(
			executable="./ffmpeg.exe",
			source=song_path,
			options="-ss " + bot.umq_last_song_ts
		))
		await message.channel.send("Replaying last song...")
	else:
		await message.channel.send("No song to replay!")

async def upload_splashes_to_burner_channel(burner_channel: discord.TextChannel):
	image_links_mapping = {}
	with open(SPLASH_LINK_MAPPINGS_FILE, 'r') as f:
		image_links_mapping = json.load(f)

	with open(SKINS_DATAFILE, 'r') as f:
		skins_data = json.load(f)
		for k,v in skins_data.items():
			if k + 'A' in image_links_mapping: # already have it, but find a better way than k + 'A'
				continue
			splash_name = v["splash_name"]
			im = Image.open(os.path.join(CHAMP_SPLASH_FOLDER, splash_name))
			x, y = im.size

			fnames_batch = []
			for letter in ['A', 'B', 'C', 'D']:
				cropped = im.crop(coordinates(letter, x, y))
				cropped.save(f"temp{letter}.jpg", "jpeg")
				fnames_batch.append(discord.File(f"temp{letter}.jpg"))
			
			# Upload this batch
			print(fnames_batch)
			burn_msg = await burner_channel.send(f'{k}', files=fnames_batch)

			print(burn_msg.attachments)
			for a, letter in zip(burn_msg.attachments, ['A', 'B', 'C', 'D']):
				# get the part of URL after channel_id/
				m = re.match(CDN_PREFIX + "\d+(/\d+/.+)", a.url)
				if m is None:
					print('somehow did not work')
				cdn_suffix = m.group(1)

				image_links_mapping[k + letter] = cdn_suffix
			break
	
	with open(SPLASH_LINK_MAPPINGS_FILE, 'w') as f:
		json.dump(image_links_mapping, f)
	
