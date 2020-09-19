import os
import threading
import re
import socket

# python3 -m pip install -U .[voice] in discord.py fork

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

	import socket

	port = 60437

	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_socket.bind("localhost", port)
	while True:
		udp_socket.recv()



print(socket.gethostbyname_ex(socket.gethostname())[-1])