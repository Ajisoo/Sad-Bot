from voiceRecognition import opus

SAMPLING_RATE = 48000
CHANNELS = 2
FRAME_LENGTH = 20
SAMPLE_SIZE = 4  # (bit_rate / 8) * CHANNELS (bit_rate == 16)
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLE_SIZE

with open("C:/Users/ajc098/Desktop/bm.pcm", "rb") as pcm_file:
	data = pcm_file.read(FRAME_SIZE * 2)

print(len(data))
encoded_data = opus.Encoder().encode(data, FRAME_SIZE)
decoded_data = opus.Decoder().decode(data, FRAME_SIZE)
with open("C:/Users/ajc098/Desktop/test.pcm", "wb+") as decoded_file:
	decoded_file.write(decoded_data)