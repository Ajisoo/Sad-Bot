import requests
from bs4 import BeautifulSoup
import os
import time

base_website = "https://www.mobafire.com"
website = base_website + "/league-of-legends/abilities"

data_folder = "content" + os.path.sep


async def cmd_refresh(message, args):
	if message.author.id not in [182707904367820800, 190253188262133761] :  # Us
		return
	r = requests.get(website)
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
		image_file = open(data_folder + str(counter) + "img.png", "wb+")
		image_file.write(requests.get(base_website + image).content)
		image_file.close()

		text_file = open(data_folder + str(counter) + "info.txt", "w+")
		text_file.write(ability_name + "\n" + champ_name + "\n" + ability_key)
		text_file.close()

		counter += 1

	host_file = open(data_folder + "!len.txt", "w+")
	host_file.write(str(counter))
	host_file.close()
	await message.channel.send("All done")








