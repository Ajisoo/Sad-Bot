from datetime import datetime
import os


# AND this function with anything that isn't ready to be released yet
# so the command can only be triggered in the test server
def only_for_testing_server(guild_id) -> bool:
	return guild_id == TEST_SERVER_GUILD_ID

IN_PROD = False

ADMINS = [182707904367820800, # ajisoo
          190253188262133761, # josh
          192144504998854658, # nolo
		]

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

CONTENT_FOLDER = os.path.join("content")

GA_BASE_WEBSITE = "https://www.mobafire.com"
GA_WEBSITE = GA_BASE_WEBSITE + "/league-of-legends/abilities"

GA_FOLDER = os.path.join(CONTENT_FOLDER, "lol_ability_guesser")
GA_LEADERBOARD_FILE = os.path.join(GA_FOLDER, "leaderboard_ga.txt")

GS_FOLDER = os.path.join(CONTENT_FOLDER, "lol_splash_guesser")
GS_LEADERBOARD_FILE = os.path.join(GS_FOLDER, "leaderboard_gs.txt")
CHAMP_SPLASH_FOLDER = os.path.join(GS_FOLDER, "img", "champion", "loading")
SKINS_DATAFILE = os.path.join(GS_FOLDER, "skins.json")
RARITY_DIST_FILE = os.path.join(GS_FOLDER, 'rarity-dist.json')
CROPPED_IMAGE_FNAME = "tempCroppedSplash.jpg"
FULL_IMAGE_FNAME = "tempFullSplash.jpg"

USER_INFO_FOLDER = os.path.join(CONTENT_FOLDER, "user_info")
SPLASH_HAREM_FILE = os.path.join(USER_INFO_FOLDER, "splash-harems.json")
SPLASH_ROLL_TIMERS_FILE = os.path.join(USER_INFO_FOLDER, "splash-roll-timers.json")

RS_ID_TO_ALIAS_MAPPINGS_FILE = os.path.join(GS_FOLDER, "champion-summary.json")
GUM_FOLDER = os.path.join(CONTENT_FOLDER, "undertale_ost_guesser")
GUM_LEADERBOARD_FILE = os.path.join(GUM_FOLDER, "leaderboard_gum.txt")

GS_LEADERBOARD_ID = "GS"
GA_LEADERBOARD_ID = "GA"
GUM_LEADERBOARD_ID = "GUM"

TEST_SERVER_GUILD_ID = 486266124351307786
LOUNGE_GUILD_ID = 190241147539423234


BURNER_IMAGES_GUILD_ID = TEST_SERVER_GUILD_ID
BURNER_IMAGES_CHANNEL_ID_TEST = 836134062821343242 # one with jisoo and others

BURNER_IMAGES_GUILD_ID2 = 836273735102890056  # separate burner images server
BURNER_IMAGES_CHANNEL_ID_TEST2 = 836273735697956897


BURNER_IMAGES_GUILD_ID_PROD = 836143604321746944 # prod burner server
BURNER_IMAGES_CHANNEL_ID_PROD = 836143604321746947

LEADERBOARDS = {
	GS_LEADERBOARD_ID: GS_LEADERBOARD_FILE,
	GA_LEADERBOARD_ID: GA_LEADERBOARD_ID, # <-- FIXME make this the correct file eventually
	GUM_LEADERBOARD_ID: GUM_LEADERBOARD_FILE,
}
