import threading
import sys
import logging
from picovoice import Picovoice
from pvrecorder import PvRecorder
from intent_dispatcher import IntentDispatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceControl(threading.Thread):
    def __init__(
            self,
            keyword_path,
            context_path,
            access_key,
            device_index,
            control_module,
            state_manager,
            porcupine_sensitivity=0.75,
            rhino_sensitivity=0.25):
        super(VoiceControl, self).__init__()

        # Picovoice API callback
        def inference_callback(inference):
            return self._inference_callback(inference)

        self._picovoice = Picovoice(
            access_key=access_key,
            keyword_path=keyword_path,
            wake_word_callback=self._wake_word_callback,
            context_path=context_path,
            inference_callback=inference_callback,
            porcupine_sensitivity=porcupine_sensitivity,
            rhino_sensitivity=rhino_sensitivity)

        self._context = self._picovoice.context_info
        self._device_index = device_index

        self._control_module = control_module
        self._state_manager = state_manager

        self._dispatcher = IntentDispatcher(self._control_module)

    def print_context(self):
        print(self._context)

    def _wake_word_callback(self):
        print('[wake word]\n')
        self._control_module.lights_handler.listen()

    def _inference_callback(self, inference):

        self._control_module.lights_handler.off()

        print('{')
        print("  is_understood : '%s'," % ('true' if inference.is_understood else 'false'))
        if inference.is_understood:
            print("  intent : '%s'," % inference.intent)
            if len(inference.slots) > 0:
                print('  slots : {')
                for slot, value in inference.slots.items():
                    print("    '%s' : '%s'," % (slot, value))
                print('  }')
        print('}\n')

        if inference.is_understood:
            # if self.state_manager.can_execute(inference.intent):
                # self._control_module.lights_handler.think()
                self._dispatcher.dispatch(inference.intent, inference.slots)
            # else:
            #     logger.warning(f"Cannot execute '{inference.intent}' while in state '{self.state_manager.state.name}'")

                # self._control_module.lights_handler.off()
                print('\n[Listening ...]')

    def run(self):
        recorder = None

        try:
            recorder = PvRecorder(device_index=self._device_index, frame_length=self._picovoice.frame_length)
            recorder.start()

            print('[Listening ...]')

            while True:
                pcm = recorder.read()
                self._picovoice.process(pcm)

        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print('Stopping ...')
        finally:
            if recorder is not None:
                recorder.delete()

            self._picovoice.delete()

