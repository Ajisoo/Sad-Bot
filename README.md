# Sad-Bot

0. Have `python 3.7` or above and know how to code a bit. 

1. Clone repo.
2. Get your own token from the [Discord Developer Portal](https://discord.com/developers/docs/intro) and team permissions from Ajisoo on said portal.
3. Get yourself invited to the testing server.
4. Copy token into a file called `bot.key` in the same directory as `bot.py`.
5. Install dependencies with `pip install -r requirements.txt`.
6. Run `python3 bot.py`. 

## External Dependencies
- `ffmpeg` must be available as a binary *in the current directory* named `ffmpeg.exe` (don't ask why)
- `opus` audio codecs must be installed in your path in order to play audio files (see [docs](https://discordpy.readthedocs.io/en/stable/api.html#discord.VoiceClient)) -- on ubuntu, you can get them with `sudo apt install opus-tools`
