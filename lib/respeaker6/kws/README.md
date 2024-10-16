## snowboy_old

```
sudo apt-get install swig libatlas-base-dev build-essential make
cd snowboy_old
python setup.py build
pip install wheel
python setup.py bdist_wheel
pip install dist/snowboy*.whl
git clone https://github.com/voice-engine/voice-engine.git
cd voice-engine
python setup.py bdist_wheel
pip install dist/*.whl
```

```
cd ~/voice-engine/examples/respeaker_6mic_array_for_pi/
python kws_doa.py
```