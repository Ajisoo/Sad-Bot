import datetime
import asyncio
import random
import re
import threading

import discord
from discord.ext import tasks

from data.bot_status import BotStatus
from commands import (
	guess_util,
	leaderboard_util,
	roll_color,
	roll_splashes,
	message_guess,
	apex_util,
)
from commands.tictactoe_util import cmd_tictactoe
from Franklin import get_franklin, Franklin
from globals import *

client = discord.Client(intents=discord.Intents.all())
bots = {}
burner_channel = None
alpha_regex = re.compile("^[a-zA-Z]+$")

async def get_bot(guild_id):
	return bots[guild_id]


def update_ga_leaderboard_file_name():
	try:
		open(os.path.join(GA_FOLDER, "leaderboard.txt"), "r")
	except Exception:
		return

	os.rename(os.path.join(GA_FOLDER, "leaderboard.txt"), GA_LEADERBOARD_FILE)


@client.event
async def on_ready():
	global bots, IN_PROD, burner_channel
	for guild in client.guilds:
		bots[guild.id] = BotStatus(client, guild)
		if guild.id == LOUNGE_GUILD_ID:
			IN_PROD = True

	if IN_PROD:
		burner_channel = client.get_channel(BURNER_IMAGES_CHANNEL_ID_PROD)
		bot_spam_channel = client.get_channel(BOT_SPAM_CHANNEL_ID)
	else:
		burner_channel = client.get_channel(BURNER_IMAGES_CHANNEL_ID_TEST)
		bot_spam_channel = client.get_channel(TEST_SPAM_CHANNEL_ID)
	
	print(f"We have logged in as {client.user}")
	if datetime.now().date() == PATCH_DAY.date():
		update_ga_leaderboard_file_name()

	roll_color.create_user_data_file()
	roll_splashes.create_user_data_files()


	now = datetime.now()
	if now.date() == PATCH_DAY.date():
		await bot_spam_channel.send(PATCH_MESSAGE_HEADER + PATCH_MESSAGE)

	os.makedirs(API_KEY_DIR, exist_ok=True)
	missing_key = False
	for key_prefix in API_KEY_NAMES:
		if not os.path.isfile(os.path.join(API_KEY_DIR, f"{key_prefix}.key")):
			missing_key = True
			print("- MISSING API KEY:", f"{key_prefix}.key")
	if missing_key:
		print("===== WARNING: At least one API key is missing (see above) =====")
		

@client.event
async def on_message(message: discord.Message):
	if message.guild is None:
		return  # we are in PM

	bot = await get_bot(message.guild.id)

	if message.author == client.user:
		return  # we are ourself

	now = datetime.now()


	if message.author.status == discord.Status.dnd:
		try:
			await message.add_reaction(await message.guild.fetch_emoji(634171978420322335))
		except:
			pass
			#await message.add_reaction(await message.guild.fetch_emoji(851961972840726578))

	if message.author.id in BIRTHDAYS.keys() and BIRTHDAYS[message.author.id][0] == now.month and BIRTHDAYS[message.author.id][1] == now.day:
		await message.add_reaction('🍰')
		if now.month == 3 and now.day == 14:
			await message.add_reaction('🥧')

	if len(message.content) < bot.essay_mode_minimum and bot.essay_mode_on and bot.essay_mode_minimum > 0:
		try:
			emji = await message.guild.fetch_emoji(883078527203827763) # feel better
			await message.add_reaction(emji)
		except Exception:
			pass
		await message.delete(delay=0.3)

	if now.month == 12 and now.day == 25:
		reactions = ['🎅', '🤶', '❄️', '⛄', '🎄', '🎁', '☃️']
		weights = [500, 500, 500, 500, 500, 500, 1]
		await message.add_reaction(random.choices(reactions, weights=weights, k=1)[0])
	
	if (message.guild.id == LOUNGE_GUILD_ID and JAIL_ROLE in [y.id for y in message.author.roles]):
		try:
			if (message.guild.id == TEST_SERVER_GUILD_ID): # test server
				await message.add_reaction(await message.guild.fetch_emoji(834785299292487701))
			else:
				await message.add_reaction(await message.guild.fetch_emoji(831228255063244831))  # shork reacc for jail
		except discord.HTTPException as he:
			if (he.text == "Reaction blocked" and he.code == 90001):
				#await message.delete(delay=0.3)
				await message.channel.send(await message.guild.fetch_emoji(831228255063244831))

	if (
		message.clean_content.strip().lower() == message_guess.MGUESS_SLEEPER_PHRASE
		and message.author.id in message_guess.MGUESS_SLEEPER_CONTACTS
	):
		# Workaround for discord.py 1.7 not having scheduling
		if message_guess.MGUESS_DINGDONG_SEND_DT.date() == datetime.now().date():
			await message_guess.cmd_mguess_dingdong(client)
			return
	
	args = []
	if message.content[:len(BOT_PREFIX)] == BOT_PREFIX:
		args = message.content[len(BOT_PREFIX):].split(' ')
		if len(args[0]) == 0:
			args = args[1:] if len(args) > 1 else []
	else:
		return

	if len(args) == 0:
		return

	args_unnormalized = args[1:] if len(args) > 1 else []
	args = [x.lower() for x in args]
	command = args[0].lower()
	args = args[1:] if len(args) > 1 else []

	if command == "die" and message.author.id in ADMINS:
		client.close()
		return

	if command == "help":
		await message.author.send(HELP_DEFAULT_MESSAGE)

	if command == "essaymode":
		if message.author.id in ESSAY_MODE_ADMINS:
			if args[0] == "on" and int(args[1]) > 0:
				bot.essay_mode_on = True
				bot.essay_mode_minimum = int(args[1])
				await message.add_reaction('✅')
			if args[0] == "off":
				bot.essay_mode_on = False
				bot.essay_mode_minimum = 0
				await message.add_reaction('✅')
		else:
			await message.channel.send("Please apply for privileges to use this command.")

	if command in ['beef', 'wrong']:
		try:
			vc = await message.author.voice.channel.connect()

		except Exception:
			vc = client.voice_clients[0]
		vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=os.path.join(CONTENT_FOLDER, 'beef.mp3')))
		vc.source = discord.PCMVolumeTransformer(vc.source)
		vc.source.volume = 0.6
		while vc.is_playing():
			await asyncio.sleep(0.1)
		# disconnect after the player has finished
		vc.stop()
		await vc.disconnect()

	if command == 'ga_refresh':
		await guess_util.cmd_ga_refresh(bot, message, args)

	if command in ['gs_refresh', 'rs_refresh']:
		await guess_util.cmd_gs_refresh(bot, message, args)

	if command == 'ga_lb':
		await message.channel.send(leaderboard_util.get_leaderboard(GA_LEADERBOARD_ID))

	if command == 'gs_lb':
		await message.channel.send(leaderboard_util.get_leaderboard(GS_LEADERBOARD_ID))

	if command in ['gum_lb', 'umq_lb']:
		await message.channel.send(leaderboard_util.get_leaderboard(GUM_LEADERBOARD_ID))

	if command == 'ga_my_score':
		await message.channel.send(leaderboard_util.get_my_points(message.author.id, GA_LEADERBOARD_ID))
	
	if command == 'gs_my_score':
		await message.channel.send(leaderboard_util.get_my_points(message.author.id, GS_LEADERBOARD_ID))

	if command == ['gum_my_score', 'umq_my_score']:
		await message.channel.send(leaderboard_util.get_my_points(message.author.id, GUM_LEADERBOARD_ID))

	if command in ['guess_ability', 'ga']:
		if len(args) > 0 and args[0] == "refresh":
			await guess_util.cmd_ga_refresh(bot, message, args)
			return
		await guess_util.cmd_ga_start(bot, message, args)

	if command in ['guess', 'g']:
		await guess_util.cmd_guess(bot, message, args)

	if command in ['giveup', 'gu', 'give_up']:
		await guess_util.cmd_give_up(bot, message, args)

	if command == 'roll':
		dice = args[0]

		if not re.match("d[1-9][0-9]*", dice):
			await message.channel.send("Use format `roll d<number>` to roll a die.")
			return

		die_number = int(dice[1:])
		rand = random.randint(1, die_number)

		await message.channel.send(f"<@{message.author.id}> rolled {rand}!")

	if command in ['tictactoe', 'ttt']:
		await cmd_tictactoe(bot, client.user, message, args)

	if command in ['playmp3']:
		try:
			vc = await message.author.voice.channel.connect()

		except Exception:

			vc = client.voice_clients[0]
		vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=os.path.join(CONTENT_FOLDER,args[0] + '.mp3')))
		while vc.is_playing():
			await asyncio.sleep(1)
		# disconnect after the player has finished
		vc.stop()
		await vc.disconnect()
		
	if command in ['bakamitai', 'bm']:
		try:
			vc = await message.author.voice.channel.connect()

		except Exception:

			vc = client.voice_clients[0]
		vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=os.path.join(CONTENT_FOLDER,'baka_mitai.mp3')))
		while vc.is_playing():
			await asyncio.sleep(1)
		# disconnect after the player has finished
		vc.stop()
		await vc.disconnect()

	if command in ['guess_undertale', 'gum', 'umq', 'undertale_music_quiz']:
		await guess_util.cmd_umq_start(bot, message, args)

	if command in ['guess_undertale_replay', 'gumr', 'umqr']:
		await guess_util.cmd_umq_replay(bot, message, args)

	if command in ['disconnect', 'dc']:
		await message.guild.voice_client.disconnect()

	if command == 'join':
		vc = await message.author.voice.channel.connect()

	if command in ['patch_notes', 'pn']:
		await message.channel.send(PATCH_MESSAGE)

	MGuessCommands = message_guess.MGuessCommands

	if command == MGuessCommands.NEW or command == "mgamr":
		await message_guess.cmd_mguess_new_game(client, message.channel, punish_on_fail=False)

	if command == MGuessCommands.SKIP:
		await message_guess.cmd_mguess_skip(message)

	if command == MGuessCommands.HINTS:
		await message_guess.cmd_mguess_hints(message)

	if command == MGuessCommands.MESSAGE:
		await message_guess.cmd_mguess_message(message)

	if command == MGuessCommands.GUESS:
		await message_guess.cmd_mguess_guess(message, args_unnormalized)

	if command == MGuessCommands.HELP:
		await message_guess.cmd_mguess_help(message)

	if command in ['guess_splash', 'gs']:
		await guess_util.cmd_gs_start(bot, message, args)

	if command in ['roll_color', 'rc']:
		await roll_color.first_time_setup(bot)
		await roll_color.cmd_roll(bot, message, args)

	if command in ['show_color', 'c', 'color']:
		await roll_color.first_time_setup(bot)
		if len(args) > 0 and args[0] == 'list':
			await roll_color.cmd_list_color(bot, message, args[1:])
		else:
			await roll_color.cmd_show_color(bot, message, args)

	if command in ['color_list', 'list_color', 'cl', 'lc']:
		await roll_color.first_time_setup(bot)
		await roll_color.cmd_list_color(bot, message, args)
	
	if command in ['rs', 'roll_splash']:
		if len(args) == 2 and message.author.id in ADMINS:
			await roll_splashes.force_roll(bot, message, args[0], args[1])
		else:
			await roll_splashes.cmd_splash_roll(bot, message)
	
	if command == 'harem':
		await roll_splashes.cmd_splash_list(bot, message, args, client)
	
	if command in ['ds', 'divorce_splash']:
		if len(args) > 0:
			await roll_splashes.divorce_splash(bot, message, args)
		else:
			await message.channel.send("Divorcee(s) not specified!")

	if command in ['is', 'info_splash']:
		if len(args) > 0:
			await roll_splashes.info_splash(bot, message, args)
		else:
			await message.channel.send("Requested champ not specified!")

	if command in ['ts', 'trade_splash']:
		if len(args) in [1,3]:
			await roll_splashes.trade_splashes(bot, message, args)
		else:
			await message.channel.send(("Please follow one of the trading formats:\n"
										"Trade initiation:\n"
										"`[$ts | $trade_splash] <@tradee> <skin_to_trade_id> <skin_to_receive_id>`\n\n"
										"Trade response:\n"
										"`[$ts] <y|yes|n|no>`"))

	if command == 'searchall':
		if len(args) > 0:
			await roll_splashes.search_all(bot, message, args, client)
		else:
			await message.channel.send("Please search for something!")

	if command == 'apexmap':
		await apex_util.cmd_get_apex_map(message)


	#TODO: add command to see current trade on you?
	if command == 'punish' and message.author.id in ADMINS:
		await roll_splashes.punish(bot, message, args)

	if command in ['test'] and only_for_testing_server(message.guild.id):
		await guess_util.upload_splashes_to_burner_channel(burner_channel)

	if command in ['create_poll', 'poll']:
		if len(args) == 0:
			await message.channel.send("Format: " + BOT_PREFIX + "create_poll <description> " + BOT_PREFIX + " <option 1 text> " + BOT_PREFIX + " <option 2 text> ...")
			return
		poll_args = " ".join(args).split(BOT_PREFIX)
		if len(poll_args) < 2:
			await message.channel.send("Format: " + BOT_PREFIX + "create_poll <description> " + BOT_PREFIX + " <option 1 text> " + BOT_PREFIX + " <option 2 text> ...")
			return
		if len(poll_args) > 10:
			await message.channel.send("Maximum of 9 options")
			return

		print(poll_args)
		description = ""
		for index in range(len(poll_args[1:])):
			description += REACTION_MAP[index + 1] + poll_args[index + 1].strip() + "\n"
		embed = discord.Embed(title=poll_args[0].strip(), description=description)
		msg = await message.channel.send(embed=embed)
		reactions = []
		for index in range(len(poll_args[1:])):
			await msg.add_reaction(REACTION_MAP2[index + 1])
			reactions.append(REACTION_MAP2[index + 1])

		def dummy(a, b, c, d):
			pass

		functions = [dummy] * len(poll_args[1:])
		Franklin(bot, msg, reactions, functions, None, lifespan=60*60*24, remove_valid_reactions=False)

@client.event
async def on_raw_reaction_add(payload):
	if payload.guild_id is None:
		return  # In PM
	bot = await get_bot(payload.guild_id)

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

dingdong_ran = False
dingdong_lock = threading.Lock()

@client.event
async def on_reaction_add(reaction, _user):
	global dingdong_ran
	# Handle dingdongbingbong
	message = reaction.message
	if message.id == message_guess.dingdong_id:
		dingdong_lock.acquire()
		if len(message.reactions) >= message_guess.MGUESS_REACT_THRESH and not dingdong_ran:
			dingdong_ran = True
			dingdong_lock.release()
			await message_guess.cmd_mguess_first_new_game(client, message.channel)
		else:
			dingdong_lock.release()

# Currently only used for $harem scrolling
@client.event
async def on_raw_reaction_remove(payload):
	if payload.guild_id is None:
		return  # In PM
	bot = await get_bot(payload.guild_id)

	if client.user.id == payload.user_id:  # Don't respond to your own reactions
		return

	reaction = payload.emoji
	message_id = payload.message_id
	franklin = get_franklin(bot, message_id)

	processed_emoji = reaction.name

	if franklin is not None:
		await franklin.remove_reaction(processed_emoji)

key_file = open("bot.key", "r")
key = key_file.readline().strip()
key_file.close()

client.run(key)
