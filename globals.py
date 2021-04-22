from datetime import datetime
import os



BOT_PREFIX = "$"

BOT_KEY_FILE = "bot.key"

BIRTHDAYS = {225822313550053376: [3, 14],
			 167090536602140682: [7, 21],
			 191597928090042369: [8, 3],
			 193550776340185088: [11, 20],
			 363197965306953730: [9, 2],
			 182707904367820800: [11, 2],
			 190248352053460993: [5, 26],
			 96079507659694080: [5, 17],
			 190253188262133761: [4, 17],
			 285290000395010048: [7, 30],
			 188670149103058944: [8, 24],
			 241766036444151808: [2, 13],
			 377691228977889283: [2, 17]}


PATCH_MESSAGE_HEADER = "🎉 New patch today 🎉\n"

PATCH_MESSAGE = ("Welcome to the Boobs and Bulge Emporium! \n"
				 "Step right up with `$gs` to get started on guessing your favorite champ skin splashes! \n"
				 "There will be a separate leaderboard for these perverts. \n"
				 "Further updates: `$ga` and `$gs` will start an ability / splash guess respectively, and \n"
				 "`$g` will be used to take a guess at the most recent guessing round that has started. \n"
				 "`$ga_lb`, `$gs_lb`, `$ga_my_score`, and `$gs_my_score` can be used to fetch scores. \n")

PATCH_DAY = datetime(2020, 10, 1)

HELP_DEFAULT_MESSAGE = "😠 no help for you! 😠"

# Folder names are relative to the location of bot.py, so if anything gets moved around make sure to update these

CONTENT_FOLDER = "content" + os.path.sep

GA_BASE_WEBSITE = "https://www.mobafire.com"
GA_WEBSITE = GA_BASE_WEBSITE + "/league-of-legends/abilities"

GA_FOLDER = CONTENT_FOLDER + "lol_ability_guesser" + os.path.sep
GA_LEADERBOARD_FILE = GA_FOLDER + "leaderboard_ga.txt"

GS_FOLDER = CONTENT_FOLDER + "lol_splash_guesser" + os.path.sep
GS_LEADERBOARD_FILE = GS_FOLDER + "leaderboard_gs.txt"

GUM_FOLDER = os.path.join(CONTENT_FOLDER, "undertale_ost_guesser")
GUM_LEADERBOARD_FILE = GUM_FOLDER + "leaderboard_gu.txt"

GS_LEADERBOARD_ID = "GS"
GA_LEADERBOARD_ID = "GA"
GUM_LEADERBOARD_ID = "GU"

LEADERBOARDS = {
	GS_LEADERBOARD_ID: GS_LEADERBOARD_FILE, # ???
	GA_LEADERBOARD_ID: GA_LEADERBOARD_ID,
	GUM_LEADERBOARD_ID: GUM_LEADERBOARD_ID,
}
