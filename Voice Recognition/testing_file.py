import socket

port = 60437

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind("localhost", port)
while True:
	udp_socket.recv()