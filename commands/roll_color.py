import os
import datetime
import discord
import random

# Example data: user_id:star_value:rgb
# Example data: 12335123421:5|255|255|255


def create_user_data_file():
	if not os.path.exists("content/roll_color/user_data.txt"):
		with open("content/roll_color/user_data.txt", "w+") as f:
			pass


async def update_file(data):
	with open("content/roll_color/user_data.txt", "w") as f:
		for key in data.keys():
			f.write(str(key) + ":" + data[key] + "\n")


async def cmd_roll(bot, message, args):
	if bot.start_date is None:
		if os.path.exists("content/roll_color/roll_start_date.txt"):
			with open("content/roll_color/roll_start_date.txt", "r") as f:
				bot.start_date = datetime.datetime.strptime(f.readline(), '%Y-%m-%d %H:%M:%S')
		else:
			bot.start_date = datetime.datetime.strptime('2021-01-17 00:00:00', '%Y-%m-%d %H:%M:%S')
			with open("content/roll_color/roll_start_date.txt", "w+") as f:
				f.write(str(bot.start_date))

	if (datetime.datetime.now() - bot.start_date).days >= 1:
		print("Updated date")
		with open("content/roll_color/user_data.txt", "w+") as f:
			bot.roll_user_data = None
		bot.start_date = bot.start_date + datetime.timedelta(days=int((datetime.datetime.now() - bot.start_date).days / 1))
		with open("roll_start_date.txt", "w+") as f:
			f.write(str(bot.start_date))

	if bot.roll_user_data is None:
		print("loading user data")
		bot.roll_user_data = {}
		with open("content/roll_color/user_data.txt", "r") as f:
			lines = f.readlines()
			for line in lines:
				user_id = line.split(":")[0]
				data = line.split(":")[1]
				bot.roll_user_data[int(user_id)] = data

	if message.author.id in bot.roll_user_data.keys():
		data = bot.roll_user_data[message.author.id].split("|")
		r = data[1]
		g = data[2]
		b = data[3]
		if data[0] == "0":
			embed = discord.Embed(title=message.author.name + ", you have already rolled!",
								  description="You currently have a 0 star color. That's impressive.")
		else:
			embed = discord.Embed(title=message.author.name + ", you have already rolled!",
								  description="You currently have a " + data[
									  0] + " star color! It has RGB value " + r + " " + g + " " + b + ". View it on the left of this message!",
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
			while not (r in [0, 255] and g in [0, 255] and b in [0, 255]):
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
			while not (r in [0, 64, 128, 192, 255] and g in [0, 64, 128, 192, 255] and b in [0, 64, 128, 192, 255]):
				r = random.randint(0, 255)
				g = random.randint(0, 255)
				b = random.randint(0, 255)
			data[1] = str(r)
			data[2] = str(g)
			data[3] = str(b)
		else:
			data = ["0", "0", "0", "0"]

		r = data[1]
		g = data[2]
		b = data[3]
		if data[0] == "0":
			embed = discord.Embed(title=message.author.name + ", you rolled a 0 star color! Impressive!",
								  description="View it on the left.")
		else:
			embed = discord.Embed(title=message.author.name + ", you rolled a " + data[0] + " star color!",
								  description="You currently have a " + data[
									  0] + " star color! It has RGB value " + r + " " + g + " " + b + ". View it on the left of this message!",
								  color=discord.Color.from_rgb(int(r), int(g), int(b)))
		await message.channel.send(embed=embed)
		bot.roll_user_data[message.author.id] = data[0] + "|" + data[1] + "|" + data[2] + "|" + data[3]
		await update_file(bot.roll_user_data)