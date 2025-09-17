import pyaudio

p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)

    if int(info["maxInputChannels"]) > 0:
        print(f"Input Device {i}: {info['name']}, Channels: {info['maxInputChannels']}")
    else:
        print(f"Output Device {i}: {info['name']}")
