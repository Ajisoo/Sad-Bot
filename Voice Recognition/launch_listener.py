import os
import threading
import re


async def start_listener(bot):
	bot.listener = threading.Thread(target=listen, args=[bot], daemon=True)
	bot.listener.start()


def listen(bot):
	port_string = os.popen('netstat -tulpn | grep "python3"').read()
	port_string = port_string[port_string.find('0.0.0.0:')+8:]
	port = int(port_string[:5])
	while bot.listener is not None:
		pass


async def stop_listener(bot):
	bot.listener = None
