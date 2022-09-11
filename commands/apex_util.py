# import discord
import datetime as dt

import requests

from globals import get_key, API_ENDPOINTS

next_time_to_refresh = None
cached_current_map = None
cached_next_map = None

def update_apex_map(now):
	"""
	Performs the API call to get the current apex map, or retrieves
	the cached value.

	Returns the name of the map on success (used by the LFG command)
	or None on failure.
	"""
	# should probably be made atomic somehow but who cares
	global next_time_to_refresh
	global cached_current_map
	global cached_next_map
	# Check cached map data
	if next_time_to_refresh is None or now >= next_time_to_refresh:
		key = get_key("apex")
		endpoint_url = API_ENDPOINTS["apex_map"]
		r = requests.get(endpoint_url, headers={"Authorization": key})
		if r.status_code == 200:
			json = r.json()
			cached_current_map = json["current"]["map"]
			curr_map_end_ms = json["current"]["end"]
			cached_next_map = json["next"]["map"]
			next_time_to_refresh = dt.datetime.fromtimestamp(curr_map_end_ms)
		else:
			cached_current_map = None
			cached_next_map = None
			next_time_to_refresh = None
	return cached_current_map

async def cmd_get_apex_map(message):
	now = dt.datetime.now()
	if update_apex_map(now) is None:
		await message.channel.send("Unable to retrieve map rotation :)")
	remaining = next_time_to_refresh - now
	hours, remainder = divmod(remaining.total_seconds(), 3600)
	minutes, seconds = divmod(remainder, 60)
	formatted = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
	await message.channel.send(
		f"Current map is **{cached_current_map}** (**{formatted}** remaining; next map is **{cached_next_map}**)")
