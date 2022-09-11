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

ESSAY_MODE_ADMINS = ADMINS + [190248352053460993] # christian bc he requested this

BOT_PREFIX = "$"

BOT_KEY_FILE = "bot.key"

API_KEY_DIR = "api_keys/"
# Each entry NAME in this list will have a corresponding API key stored in `api_keys/NAME.key`
API_KEY_NAMES = [
	"apex",
]


def get_key(key_name):
	"""Returns the key text corresponding to the provided key name; errors on failure."""
	with open(os.path.join(API_KEY_DIR, f"{key_name}.key")) as f:
		return f.read().strip()


# Maps an endpoint URL to some simple name
API_ENDPOINTS = {
	"apex_map": "https://api.mozambiquehe.re/maprotation",
}

BIRTHDAYS = {225822313550053376: [3, 14],
			 167090536602140682: [7, 21],
			 191597928090042369: [8, 3],
			 193550776340185088: [11, 20],
			 363197965306953730: [9, 2],
			 193787631325151238: [6, 16],
			 182707904367820800: [11, 2],
			 190248352053460993: [5, 26],
			 96079507659694080: [5, 17],
			 259454924964757504: [9, 22],
			 190253188262133761: [4, 17],
			 285290000395010048: [7, 30],
			 734705037489733692: [7, 30],
			 188670149103058944: [8, 24],
			 241766036444151808: [2, 13],
			 157724394767122432: [7, 11],
			 497278780721725440: [10, 31],
			 123460317463183363: [11, 9],
			 262490582276898816: [11, 10],
			 112703359890227200: [5, 23],
			 192144504998854658: [7, 22],
			 377691228977889283: [2, 17]}

JAIL_ROLE = 824551576336990211

PATCH_MESSAGE_HEADER = "🎉 Patch 2.2 released today 🎉\n"

PATCH_MESSAGE = ("New command $essaymode is here!\n"
				"Tired of people typing short messages?\n"
				"Use `$essaymode on [numChars]` to set a minimum of characters everyone needs to type!\n"
				"Use `$essaymode off` to disable essay mode.\n")

PATCH_DAY = datetime(2021, 12, 1)

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
SPLASH_LINK_MAPPINGS_FILE = os.path.join(USER_INFO_FOLDER, "image-links.json")

TENTH_ANNIVERSARY_SKINS_FOLDER = os.path.join(CONTENT_FOLDER, "anniversary_skins")
TENTH_ANNIVERSARY_SKINS_JSON = os.path.join(USER_INFO_FOLDER, "anniversary_skins.json")

RS_ID_TO_ALIAS_MAPPINGS_FILE = os.path.join(GS_FOLDER, "champion-summary.json")
RS_SKIN_NAME_TO_ID_MAPPINGS_FILE = os.path.join(GS_FOLDER, "name-to-id-mappings.json")
GUM_FOLDER = os.path.join(CONTENT_FOLDER, "undertale_ost_guesser")
GUM_LEADERBOARD_FILE = os.path.join(GUM_FOLDER, "leaderboard_gum.txt")

LFG_FILE = os.path.join(CONTENT_FOLDER, "lfg.json")

GS_LEADERBOARD_ID = "GS"
GA_LEADERBOARD_ID = "GA"
GUM_LEADERBOARD_ID = "GUM"

TEST_SERVER_GUILD_ID = 486266124351307786
LOUNGE_GUILD_ID = 190241147539423234
BOT_SPAM_CHANNEL_ID = 390742885693390849
TEST_SPAM_CHANNEL_ID = 486266124351307789

# prefix + burn_server_id + /image_id + /image_name
CDN_PREFIX = "https://cdn.discordapp.com/attachments/"

BURNER_IMAGES_GUILD_ID = TEST_SERVER_GUILD_ID
BURNER_IMAGES_CHANNEL_ID_TEST = 836343014032801912  # one with jisoo and others

BURNER_IMAGES_GUILD_ID2 = 836273735102890056  # separate burner images server
BURNER_IMAGES_CHANNEL_ID_TEST2 = 836273735697956897

BURNER_IMAGES_GUILD_ID_PROD = 836143604321746944 # prod burner server
BURNER_IMAGES_CHANNEL_ID_PROD = 836143604321746947

LEADERBOARDS = {
	GS_LEADERBOARD_ID: GS_LEADERBOARD_FILE,
	GA_LEADERBOARD_ID: GA_LEADERBOARD_ID, # <-- FIXME make this the correct file eventually
	GUM_LEADERBOARD_ID: GUM_LEADERBOARD_FILE,
}

RARITY_DIST = {
	"kNoRarity": {
		'percentage': 0.75,
		'rolls': []
	},
	"kEpic": {
		'percentage': 0.20,
		'rolls': []
	},
	"kLegendary": {
		'percentage': 0.02,
		'rolls': []
	},
	"kUltimate": {
		'percentage': 0.01,
		'rolls': []
	},
	"kMythic": {
		'percentage': 0.02,
		'rolls': []
	}
}

REACTION_MAP = {
	0: ":zero:",
	1: ":one:",
	2: ":two:",
	3: ":three:",
	4: ":four:",
	5: ":five:",
	6: ":six:",
	7: ":seven:",
	8: ":eight:",
	9: ":nine:",
}
REACTION_MAP2 = {
	0: "0⃣",
	1: "1⃣",
	2: "2⃣",
	3: "3⃣",
	4: "4⃣",
	5: "5⃣",
	6: "6⃣",
	7: "7⃣",
	8: "8⃣",
	9: "9⃣",
}
