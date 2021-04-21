import os
import datetime
import discord
import random
import time
from PIL import Image

# Example data: user_id:rolled_this_week: star_value|r|g|b, star_value|r|g|b
# Example data: 12335123421:1:5|255|255|255,4|128|128|128


def create_user_data_file():
	if not os.path.exists("content/roll_color/user_data.txt"):
		os.makedirs("content/roll_color/")
		with open("content/roll_color/user_data.txt", "w+") as f:
			pass

stars = {"5": ":star2: :star2: :star2: :star2: :star2:", "4": ":star: :star: :star: :star:", "3": ":star: :star: :star:", "0": ""}

async def cmd_show_color(bot, message, args):
	color_size = {"5": 500, "4": 200, "3": 100, "0":2}
	val = 0
	if len(args) > 0 and (args[0][0] == '-' or args[0][0].isdigit()) and (len(args[0]) == 1 or args[0][1:].isdigit()):
		val = int(args[0])
	if val < 0 or val >= len(bot.roll_user_data[message.author.id][1]):
		await message.channel.send("Bad index. Try again.")
		return
	data = bot.roll_user_data[message.author.id][1][val].split("|")
	if val == 0:
		title = message.author.name + "'s current Color!\n"
	else:
		title = message.author.name + "'s Color!\n"
	title += stars[data[0]] + " RGB " + data[1] + " " + data[2] + " " + data[3]
	img = Image.new('RGB', (color_size[data[0]], color_size[data[0]]), (max(0,int(data[1])), max(0, int(data[2])), max(0, int(data[3]))))
	img.save("content/color.jpg")
	file = discord.File("content/color.jpg")
	await message.channel.send(title, file=file)


async def cmd_list_color(bot, message, args):
	prefix = ""
	valid = []
	if len(args) > 0 and args[0] == '5s':
		prefix = "'s 5 Star Colors:\n"
		for i in range(len(bot.roll_user_data[message.author.id][1])):
			if bot.roll_user_data[message.author.id][1][i].split("|")[0] == "5":
				valid.append((i, bot.roll_user_data[message.author.id][1][i]))
		args = args[1:]
	elif len(args) > 0 and args[0] == '4s':
		prefix = "'s 4 Star Colors:\n"
		for i in range(len(bot.roll_user_data[message.author.id][1])):
			if bot.roll_user_data[message.author.id][1][i].split("|")[0] == "4":
				valid.append((i, bot.roll_user_data[message.author.id][1][i]))
		args = args[1:]
	elif len(args) > 0 and args[0] == '3s':
		prefix = "'s 3 Star Colors:\n"
		for i in range(len(bot.roll_user_data[message.author.id][1])):
			if bot.roll_user_data[message.author.id][1][i].split("|")[0] == "3":
				valid.append((i, bot.roll_user_data[message.author.id][1][i]))
		args = args[1:]
	elif len(args) > 0 and args[0] == '0s':
		prefix = "'s 0 Star Colors:\n"
		for i in range(len(bot.roll_user_data[message.author.id][1])):
			if bot.roll_user_data[message.author.id][1][i].split("|")[0] == "0":
				valid.append((i, bot.roll_user_data[message.author.id][1][i]))
		args = args[1:]
	else:
		prefix = "'s Colors:\n"
		for i in range(len(bot.roll_user_data[message.author.id][1])):
			valid.append((i, bot.roll_user_data[message.author.id][1][i]))

	if len(args) > 0 and (args[0][0] == '-' or args[0][0].isdigit()) and (len(args[0]) == 1 or args[0][1:].isdigit()):
		val = int(args[0])
		if val < 0:
			val += int(len(valid) / 20)
		if val != 0 and (val < 0 or val > int(len(valid) / 20)):
			await message.channel.send("Bad index. Try again.")
			return
	else:
		val = 0

	if len(valid) == 0:
		await message.channel.send("No Results.")
		return

	limit = min(20*val + 20, len(valid))
	data = valid[20*val:limit]
	string = message.author.name + "'s Colors:\n"
	for index, thing in data:
		_thing = thing.split("|")
		string += "[" + str(index) + "] " + stars[_thing[0]] + " RGB " + _thing[1] + " " + _thing[2] + " " + _thing[3] + "\n"
	await message.channel.send(string)


async def update_file(data):
	with open("content/roll_color/user_data.txt", "w") as f:
		for key in data.keys():
			f.write(str(key) + ":" + data[key][0] + ":" + ",".join(data[key][1]) + "\n")


async def first_time_setup(bot):
	if bot.start_date is None:
		if os.path.exists("content/roll_color/roll_start_date.txt"):
			with open("content/roll_color/roll_start_date.txt", "r") as f:
				bot.start_date = datetime.datetime.strptime(f.readline()[:-1], '%Y-%m-%d %H:%M:%S')
		else:
			bot.start_date = datetime.datetime.strptime('2021-01-17 00:00:00', '%Y-%m-%d %H:%M:%S')
			with open("content/roll_color/roll_start_date.txt", "w+") as f:
				f.write(str(bot.start_date) + "\n")

	if bot.roll_user_data is None:
		bot.roll_user_data = {}
		with open("content/roll_color/user_data.txt", "r") as f:
			lines = f.readlines()
			for line in lines:
				_line = line[:-1].split(":")
				user_id = _line[0]
				data = _line[1]
				colors = _line[2]
				bot.roll_user_data[int(user_id)] = (data, colors.split(","))

	if (datetime.datetime.now() - bot.start_date).days >= 1:
		with open("content/roll_color/user_data.txt", "w+") as f:
			for key in bot.roll_user_data.keys():
				bot.roll_user_data[key] = ("0", bot.roll_user_data[key][1])
		await update_file(bot.roll_user_data)
		bot.start_date = bot.start_date + datetime.timedelta(days=int((datetime.datetime.now() - bot.start_date).days / 1))
		with open("content/roll_color/roll_start_date.txt", "w+") as f:
			f.write(str(bot.start_date) + "\n")


async def cmd_roll(bot, message, args):
	if message.author.id in bot.roll_user_data.keys() and bot.roll_user_data[message.author.id][0] == "1":
		data = bot.roll_user_data[message.author.id][1][0].split("|")
		r = data[1]
		g = data[2]
		b = data[3]
		if data[0] == "0":
			embed = discord.Embed(title=message.author.name + ", you have already rolled!",
								  description="You currently have a 0 star color. That's impressive.")
		else:
			embed = discord.Embed(title=message.author.name + ", you have already rolled!",
								  description="You currently have " + stars[data[0]] + " RGB " + r + " " + g + " " + b + ". View it on the left of this message!",
								  color=discord.Color.from_rgb(int(r), int(g), int(b)))
		await message.channel.send(embed=embed)
	else:
		num = random.random()
		data = ["", "", "", ""]
		if num < 0.05:
			data[0] = "5"
			r = random.randint(0, 1)
			g = random.randint(0, 1)
			b = random.randint(0, 1)
			r *= 255
			g *= 255
			b *= 255
			data[1] = str(r)
			data[2] = str(g)
			data[3] = str(b)

		elif num < 0.35:
			data[0] = "4"
			r,g,b = (0,0,0)
			while r in [0, 255] and g in [0, 255] and b in [0, 255]:
				r = random.randint(0, 4)
				g = random.randint(0, 4)
				b = random.randint(0, 4)
				r *= 64
				g *= 64
				b *= 64
				if r == 256:
					r = 255
				if g == 256:
					g = 255
				if b == 256:
					b = 255
			data[1] = str(r)
			data[2] = str(g)
			data[3] = str(b)

		elif num < 0.995:
			data[0] = "3"
			r, g, b = (0, 0, 0)
			while r in [0, 64, 128, 192, 255] and g in [0, 64, 128, 192, 255] and b in [0, 64, 128, 192, 255]:
				r = random.randint(0, 255)
				g = random.randint(0, 255)
				b = random.randint(0, 255)
			data[1] = str(r)
			data[2] = str(g)
			data[3] = str(b)
		else:
			data = ["0", "-1", "-1", "-1"]

		r = data[1]
		g = data[2]
		b = data[3]
		base_embed = discord.Embed(title=message.author.name + ", you rolled :question: :question: :question:")
		r_embed = discord.Embed(title=message.author.name + ", you rolled ***" + r + "*** :question: :question:")
		g_embed = discord.Embed(title=message.author.name + ", you rolled ***" + r + "*** ***" + g + "*** :question:")
		b_embed = discord.Embed(title=message.author.name + ", you rolled ***" + r + "*** ***" + g + "*** ***" + b + "***")

		if message.author.id not in bot.roll_user_data.keys():
			bot.roll_user_data[message.author.id] = ("0", [])
		bot.roll_user_data[message.author.id] = ("1", bot.roll_user_data[message.author.id][1])
		bot.roll_user_data[message.author.id][1].insert(0, data[0] + "|" + data[1] + "|" + data[2] + "|" + data[3])
		await update_file(bot.roll_user_data)
		sent_embed = await message.channel.send(embed=base_embed)
		time.sleep(1)
		await sent_embed.edit(embed=r_embed)
		time.sleep(1)
		await sent_embed.edit(embed=g_embed)
		time.sleep(1)
		await sent_embed.edit(embed=b_embed)
		time.sleep(1)
		if data[0] == "0":
			embed = discord.Embed(title=message.author.name + ", you rolled a 0 star color! Impressive!",
								  description="View it on the left.")
		else:
			embed = discord.Embed(title=message.author.name + ", you rolled a " + data[0] + " star color!",
								  description="You currently have " + stars[data[0]] + " RGB " + r + " " + g + " " + b + ". View it on the left of this message!",
								  color=discord.Color.from_rgb(int(r), int(g), int(b)))
		await sent_embed.edit(embed=embed)
