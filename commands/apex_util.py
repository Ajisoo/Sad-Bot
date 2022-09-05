# import discord
import requests
import time

from bs4 import BeautifulSoup


from globals import APEX_MAP_ROTATION_SITE

next_time = None
cached_value = None


async def cmd_get_apex_map(message):
	global next_time
	global cached_value
	print("current time" + str(time.time()))
	if next_time is None or cached_value is None or next_time < time.time():
		print("no cache")
		r = requests.get(APEX_MAP_ROTATION_SITE)

		if int(r.status_code / 100) != 2:
			await message.channel.send('Error: ' + r.status_code)
			return


		soup_value = BeautifulSoup(r.content, "html.parser")

		cached_value = soup_value.find("div", {"class": "col-lg-6"}) \
						.find("div", {"onclick": "location.href = '/current-map/battle_royale/pubs';"}) \
						.find("h1")
		next_time = time.time() + 60 # 1 min
		print("new time" + str(next_time))

	await message.channel.send('Current map (' + cached_value.text + ')')


