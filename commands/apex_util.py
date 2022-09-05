# import discord
import requests

from bs4 import BeautifulSoup


from globals import APEX_MAP_ROTATION_SITE


async def cmd_get_apex_map(message):
	r = requests.get(APEX_MAP_ROTATION_SITE)

	if int(r.status_code / 100) != 2:
		return

	soup_value = BeautifulSoup(r.content, "html.parser")

	map_title = soup_value.find("div", {"class": "col-lg-6"}) \
					.find("div", {"onclick": "location.href = '/current-map/battle_royale/pubs';"}) \
					.find("h1")

	await message.channel.send('Current map (' + map_title.text + ')')


