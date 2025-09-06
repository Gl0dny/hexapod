# ODAS Audio Playback Guide

[← Previous: ODAS Data Format](odas_data_format.md) | [Next: Streaming ODAS Audio Player →](streaming_odas_audio_player.md)

[← Back to Documentation](../README.md)

## Understanding ODAS Output Files

ODAS produces several types of audio output files with different characteristics:

### Raw Input File
- Sample rate: 16000 Hz
- Bit depth: 32-bit
- Channels: 8 (for ReSpeaker 6 Mic Array)
- Format: Signed integer, little-endian

### Postfiltered Output File
- Sample rate: 44100 Hz
- Bit depth: 16-bit
- Channels: 4 (separated audio streams)
- Format: Signed integer, little-endian

## Playing Audio Files

### Playing Raw Input
```bash
play -r 16000 -b 32 -c 8 -e signed-integer -t raw input.raw
```

### Playing Postfiltered Output

The postfiltered output contains 4 channels of separated audio. Here are different ways to play it:

1. Play all 4 channels (correct speed but may be unbalanced):
```bash
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw
```

2. Mix all channels to stereo (both ears):
```bash
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 1,2,3,4 1,2,3,4
```

3. Map specific channels to left and right:
```bash
# Channels 1+2 in left, 3+4 in right
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 1,2 3,4

# Channels 1+3 in left, 2+4 in right
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 1,3 2,4
```

4. Listen to individual channels:
```bash
# Channel 1 only
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 1

# Channel 2 only
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 2

# Channel 3 only
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 3

# Channel 4 only
play -r 44100 -b 16 -c 4 -e signed-integer -t raw postfiltered.raw remix 4
```



## Notes
- The postfiltered output contains separated audio streams in 4 channels
- Different channel mappings may work better depending on your setup
- Always use the correct sample rate and channel count to maintain proper playback speed 


### My testing
**Host:**
```
scp hexapod@192.168.0.122:/home/hexapod/hexapod/postfiltered.raw .
./src/odas/convert_odas_audio.py ~/postfiltered.raw test.wav
 afplay test.wav
 ```

 **Target:**
 ```
 python src/odas/odas_server.py
 ./src/odas/convert_odas_audio.py postfiltered.raw test.wav
 ./src/odas/test_picovoice_complete.py test.wav --access-key ACCESS_KEY
 ```

---

[← Previous: ODAS Data Format](odas_data_format.md) | [Next: Streaming ODAS Audio Player →](streaming_odas_audio_player.md)

[← Back to Documentation](../README.md)