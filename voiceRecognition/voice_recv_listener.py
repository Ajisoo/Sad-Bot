
class VoiceReceiveListener:

	def __init__(self, vc):
		self.vc = vc


async def listen(vc):
	while vc.is_connected():
		#print("before_pcm")
		pcm, ssrc = await vc.recv(4096)
		if pcm is not None:
			print(pcm)
			print(ssrc)
	print("Done")