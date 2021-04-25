import discord
import datetime
import asyncio
import random
import re

from data.bot_status import BotStatus
from commands import guess_util, leaderboard_util, roll_color, roll_splashes
from commands.tictactoe_util import cmd_tictactoe
from Franklin import get_franklin
from globals import *

client = discord.Client()
bots = {}

async def get_bot(guild_id):
	global bots
	return bots[guild_id]


def update_ga_leaderboard_file_name():
	try:
		open(GA_FOLDER + "leaderboard.txt", "r")
	except Exception:
		return

	os.rename(GA_FOLDER + "leaderboard.txt", GA_LEADERBOARD_FILE)

@client.event
async def on_ready():
	global bots
	for guild in client.guilds:
		bots[guild.id] = BotStatus(client)
	print('We have logged in as {0.user}'.format(client))
	if datetime.now().date() == PATCH_DAY.date():
		update_ga_leaderboard_file_name()

	roll_color.create_user_data_file()
	roll_splashes.create_user_data_files()


@client.event
async def on_message(message: discord.Message):
	if message.guild is None:
		return  # we are in PM

	bot = await get_bot(message.guild.id)

	if message.author == client.user:
		return  # we are ourself

	now = datetime.now()

	if message.author.status == discord.Status.dnd:
		await message.add_reaction(await message.guild.fetch_emoji(634171978420322335))

	if message.author.id in BIRTHDAYS.keys() and BIRTHDAYS[message.author.id][0] == now.month and BIRTHDAYS[message.author.id][1] == now.day:
		await message.add_reaction('🍰')

	if now.month == 12 and now.day == 25:
		await message.add_reaction('🎅')
		
	args = []
	if message.content[:len(BOT_PREFIX)] == BOT_PREFIX:
		args = message.content[len(BOT_PREFIX):].split(' ')
		if len(args[0]) == 0:
			args = args[1:] if len(args) > 1 else []
	else:
		return

	if len(args) == 0:
		return

	args = [x.lower() for x in args]
	command = args[0].lower()
	args = args[1:] if len(args) > 1 else []

	if not bot.patch_message_sent and now.date() == PATCH_DAY.date():
		await message.channel.send(PATCH_MESSAGE_HEADER + PATCH_MESSAGE)
		bot.patch_message_sent = True

	if command == "help":
		await message.author.send(HELP_DEFAULT_MESSAGE)

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

		await message.channel.send(f"<@{message.author.id}> rolled 1!")

	if command in ['tictactoe', 'ttt']:
		await cmd_tictactoe(bot, client.user, message, args)

	if command in ['bakamitai', 'bm']:
		try:
			vc = await message.author.voice.channel.connect()

		except Exception:

			vc = client.voice_clients[0]
		vc.play(discord.FFmpegPCMAudio(executable="./ffmpeg.exe", source=CONTENT_FOLDER + 'baka_mitai.mp3'))
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
	
	if command in ['rs', 'roll_splash'] and only_for_testing_server(message.guild.id):
		if len(args) > 0 and only_for_testing_server(message.guild.id):
			await roll_splashes.force_roll(bot, message, args[0])
		else:
			await roll_splashes.cmd_splash_roll(bot, message)
	
	if command == 'harem' and only_for_testing_server(message.guild.id):
		await roll_splashes.cmd_splash_list(bot, message, args)
	
	if command in ['ds', 'divorce_splash'] and only_for_testing_server(message.guild.id):
		if len(args) > 0:
			await roll_splashes.divorce_splash(message, args)
		else:
			await message.channel.send("Divorcee(s) not specified!")

	if command in ['test_skins'] and only_for_testing_server(message.guild.id):
		await guess_util.debug_get_cdragon_json(bot, message, args)

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

key_file = open("bot.key", "r")
key = key_file.readline().strip()
key_file.close()

client.run(key)
