Audio processing algorithms such as Acoustic Echo Cancellation (AEC), Direction Of + Arrival (DOA), Noise Suppression (NS) and Beamforming

## AEC

In a smart speaker, the algorithm Acoustic Echo Cancellation (AEC) is used to cancel music, which is played by itself, from the audio captured by its microphones, so it can hear your voice clearly when it is playing music.

The open source library `speexdsp` has a AEC algorithm. There are two examples to use it in Python and C.

1. `pip3 install speexdsp`
2. create a python script named `ec.py`
3. play a music (for example, `music.wav`) and record it as `rec.wav`, and run `python ec.py rec.wav music.wav out.wav`.
    

**Note: only mono music is supported.** To get a good result, `music.wav` and `rec.wav` should be aligned.

 using AEC in C

See [ec](https://github.com/voice-engine/ec)


## NS

Noise Suppression (NS) is widely used in audio systems. In a smart speaker, NS is requred to remove noise without introducing too much audio distortion which is farmful to speech recognition.

Among a variety of NS algorithms, the NS in WebRTC's audio processing module is a robust one. We will use it belwow.

 NS of WebRTC Audio Processing in Python[¶](http://127.0.0.1:8000/audio_processing/ns/#ns-of-webrtc-audio-processing-in-python "Permanent link")

[python-webrtc-audio-processing](https://github.com/xiongyihui/python-webrtc-audio-processing) is used here.

1. `pip install webrtc-audio-processing`
2. create a python script named `ns.py
3. `python ns.py noisy.wav out.wav`

