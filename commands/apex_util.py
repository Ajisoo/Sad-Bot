# import discord
import datetime as dt
import time

import requests
from bs4 import BeautifulSoup

from globals import get_key, API_ENDPOINTS

curr_map_name = None
curr_map_end_ms = None
next_map_name = None
next_map_end_ms = None


async def cmd_get_apex_map(message):
	# should probably be made atomic somehow but who cares
	global curr_map_name
	global curr_map_end_ms
	global next_map_name
	global next_map_end_ms
	now = int(time.time())
	# Check cached map data
	if curr_map_end_ms is not None and now > curr_map_end_ms and next_map_end_ms is not None:
		# Use cached next map, do request later
		curr_map_name = next_map_name
		curr_map_end_ms = next_map_end_ms
		next_map_name = None
		next_map_end_ms = None
		return
	key = get_key("apex")
	endpoint_url = API_ENDPOINTS["apex_map"]
	r = requests.get(endpoint_url, headers={"Authorization": key})
	if r.status_code == 200:
		json = r.json()
		curr_map_name = json["current"]["map"]
		curr_map_end_ms = json["current"]["end"]
		next_map_name = json["next"]["map"]
		next_map_end_ms = json["next"]["end"]
		remaining = dt.datetime.fromtimestamp(curr_map_end_ms - now).strftime("%M:%S")
		await message.channel.send(f"Current map is **{curr_map_name}** (**{remaining}** remaining; next map is **{next_map_name}**)")
	else:
		await message.channel.send("Unable to retrieve map rotation :)")
