import asyncio
import concurrent.futures
import pocketsphinx
import os

from distutils.sysconfig import get_python_lib

async def load_base_decoder():
	MODELDIR = os.path.join(get_python_lib(), "pocketsphinx", "model")
	config = pocketsphinx.Decoder.default_config()
	config.set_string('-hmm', os.path.join(MODELDIR, 'en-us'))
	config.set_string('-lm', os.path.join(MODELDIR, 'en-us.lm.bin'))
	config.set_string('-dict', os.path.join(MODELDIR, 'cmudict-en-us.dict'))
	config.set_string('-keyphrase', 'sad bot')
	config.set_string('-logfn', 'nul')
	config.set_float('-kws_threshold', 1e+20)

	# Creaders decoder object for streaming data.
	decoder = pocketsphinx.Decoder(config)
	return decoder

async def listen(vc, client):
	decoders = {}
	while vc.is_connected():
		executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
		loop = asyncio.get_event_loop()
		pcm, user_id = await loop.run_in_executor(executor, vc.recv, 4096)
		if pcm is not None and user_id is not None:
			with open('C:/Users/ajc098/Desktop/my.pcm', "ab") as f:
				f.write(pcm)
			if user_id not in decoders.keys():
				decoders[user_id] = await load_base_decoder()
				decoders[user_id].start_utt()
			decoder = decoders[user_id]
			decoder.process_raw(pcm, False, False)
			if decoder.hyp() is not None:
				print([(seg.word, seg.prob, seg.start_frame, seg.end_frame) for seg in decoder.seg()])
