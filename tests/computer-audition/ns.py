import sys
import wave
from webrtc_audio_processing import AudioProcessingModule as AP

if len(sys.argv) < 3:
    print('Usage: {} noisy.wav out.wav'.format(sys.argv[0]))
    sys.exit(1)

frame_size = 256

noisy = wave.open(sys.argv[1], 'rb')
out = wave.open(sys.argv[2], 'wb')

channels = noisy.getnchannels()
sample_width = noisy.getsampwidth()  # only 16 bits is supported
rate = noisy.getframerate()

out.setnchannels(channels)
out.setsampwidth(sample_width)
out.setframerate(rate)

ap = AP(enable_vad=True, enable_ns=True)
ap.set_stream_format(rate, channels)        # set sample rate and channels
ap.set_ns_level(1)                          # NS level from 0 to 3
ap.set_vad_level(1)                         # VAD level from 0 to 3

frames_10ms = int(rate / 100)

while True:
    in_data = near.readframes(frames_10ms)
    if len(in_data) != (frames_10ms * channels * sample_width):
        break

    # only support processing 10ms audio data each time
    audio_out = ap.process_stream(in_data)

    out.writeframes(in_data)

noisy.close()
out.close()