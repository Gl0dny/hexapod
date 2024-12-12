"""Acoustic Echo Cancellation for WAV files."""

import wave
import sys
from speexdsp import EchoCanceller

# Check if the required arguments are provided
if len(sys.argv) < 4:
    print('Usage: {} near.wav far.wav out.wav'.format(sys.argv[0]))
    sys.exit(1)

# Frame size for processing
frame_size = 256

# Open the input WAV files
near = wave.open(sys.argv[1], 'rb')
far = wave.open(sys.argv[2], 'rb')

# Ensure both input files are mono-channel
if near.getnchannels() > 1 or far.getnchannels() > 1:
    print('Only mono channel audio is supported')
    sys.exit(2)

# Prepare the output WAV file with the same parameters as the 'near' file
out = wave.open(sys.argv[3], 'wb')
out.setnchannels(near.getnchannels())
out.setsampwidth(near.getsampwidth())
out.setframerate(near.getframerate())

# Print information about the input files
print('Near - rate: {}, channels: {}, length: {}'.format(
    near.getframerate(),
    near.getnchannels(),
    near.getnframes() / near.getframerate()
))
print('Far - rate: {}, channels: {}'.format(
    far.getframerate(),
    far.getnchannels()
))

# Create an EchoCanceller object
echo_canceller = EchoCanceller.create(frame_size, 2048, near.getframerate())

# Buffer size parameters
in_data_len = frame_size
in_data_bytes = frame_size * 2
out_data_len = frame_size
out_data_bytes = frame_size * 2

# Process the audio data frame by frame
while True:
    # Read frames from both input files
    in_data = near.readframes(in_data_len)
    out_data = far.readframes(out_data_len)

    # Break the loop if we have reached the end of the files
    if len(in_data) != in_data_bytes or len(out_data) != out_data_bytes:
        break

    # Perform echo cancellation on the input data
    in_data = echo_canceller.process(in_data, out_data)

    # Write the processed data to the output file
    out.writeframes(in_data)

# Close the WAV files
near.close()
far.close()
out.close()