import pyaudio
import wave
import numpy as np

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 8
RESPEAKER_WIDTH = 2
# run identify_audio_devices.py to get index
RESPEAKER_INDEX = 1  # refer to input device id
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME_TEMPLATE = "output_channel_{}.wav"

p = pyaudio.PyAudio()

# Open audio stream
stream = p.open(
    rate=RESPEAKER_RATE,
    format=p.get_format_from_width(RESPEAKER_WIDTH),
    channels=RESPEAKER_CHANNELS,
    input=True,
    input_device_index=RESPEAKER_INDEX,
    frames_per_buffer=CHUNK,
)

print("* recording")

# Initialize frames list for each channel
frames: list[list[bytes]] = [[] for _ in range(RESPEAKER_CHANNELS)]

for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    # Convert data to numpy array
    audio_data = np.frombuffer(data, dtype=np.int16)

    # Split and store the data for each channel
    for ch in range(RESPEAKER_CHANNELS):
        frames[ch].append(audio_data[ch::RESPEAKER_CHANNELS].tobytes())

print("* done recording")

# Stop and close the stream
stream.stop_stream()
stream.close()
p.terminate()

# Save each channel's data to a separate file
for ch in range(RESPEAKER_CHANNELS):
    wf = wave.open(WAVE_OUTPUT_FILENAME_TEMPLATE.format(ch), "wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
    wf.setframerate(RESPEAKER_RATE)
    wf.writeframes(b"".join(frames[ch]))
    wf.close()

print(f"Recorded 8 channels to separate files.")
