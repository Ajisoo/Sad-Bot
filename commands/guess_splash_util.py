import requests
import shutil
import os
from fnmatch import fnmatch
from globals import *

versions_endpoint = 'https://ddragon.leagueoflegends.com/api/versions.json'
data_dragon_endpoint_base = 'https://ddragon.leagueoflegends.com/cdn/dragontail-'
dumpfile_name = GS_FOLDER + 'dump.tgz'


async def cmd_guess_splash_refresh(bot, message, args):
	if message.author.id not in [182707904367820800, 190253188262133761]:  # Us
		return
	
	# Get the latest patch number
	response = requests.get(versions_endpoint)
	
	latest_version = None
	try:
		latest_version = response.json()[0]
	except Exception as e:
		print("Getting latest version has failed: " + str(e))

	bot.gs_valid = False

	# Create the data directory if not exists
	if not os.path.exists(GS_FOLDER):
		os.makedirs(GS_FOLDER)

	# Get the data dragon dump
	data_dragon_endpoint_full = data_dragon_endpoint_base + latest_version + ".tgz"
	print(data_dragon_endpoint_full)

	data_dump_response = requests.get(data_dragon_endpoint_full, stream=True)
	if response.status_code == 200:
		print("Getting data dragon dump...")
		with open(dumpfile_name, 'wb') as f:
			f.write(data_dump_response.raw.read())
		print("Done downloading data dump!")

		print("Unpacking data dump...")
		shutil.unpack_archive(dumpfile_name, GS_FOLDER)
		print("Done unpacking data dump!")

		# Remove tgz, dragonhead, languages, and lolpatch_*
		print("Removing extraneous files...")
		for file in os.listdir(GS_FOLDER):
			if fnmatch(file, "lolpatch*") or fnmatch(file, latest_version + "*"):
				shutil.rmtree(GS_FOLDER + file, ignore_errors=True)
			elif fnmatch(file, "*.json") or fnmatch(file, "*.js") or fnmatch(file, "dump.tgz"):
				os.remove(GS_FOLDER + file)
		print("Removed extraneous files!")

		print("Done, champ splashes are ready now!")

	else:
		print("Error, here is response:" + str(response))	
	



	bot.gs_valid = True 