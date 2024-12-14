import threading
import abc

class Animation(abc.ABC):
    def __init__(self, lights):
        self.lights = lights
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    @abc.abstractmethod
    def run(self):
        pass

    def stop_animation(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.01)

class AlternateRotateAnimation(Animation):
    def __init__(self, lights, color_even='indigo', color_odd='golden', delay=0.25, positions=12):
        super().__init__(lights)
        self.color_even = color_even
        self.color_odd = color_odd
        self.delay = delay
        self.positions = positions

    def run(self):
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                color = self.color_even if i % 2 == 0 else self.color_odd
                self.lights.set_color(color, led_index=i)

            for _ in range(self.positions):
                self.lights.rotate(1)
                if self.stop_event.wait(self.delay):
                    return
                
class WheelFillAnimation(Animation):
    def __init__(self, lights, use_rainbow=True, color='white', interval=0.2):
        super().__init__(lights)
        self.use_rainbow = use_rainbow
        self.color = color
        self.interval = interval

    def run(self):
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                if self.use_rainbow:
                    rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
                else:
                    rgb = self.lights.COLORS_RGB.get(self.color.lower(), (0, 0, 0))
                
                self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)

                if self.stop_event.wait(self.interval):
                    return
                
class PulseSmoothlyAnimation(Animation):
    def __init__(self, lights, base_color='blue', pulse_color='green', pulse_speed=0.05):
        super().__init__(lights)
        self.base_color = base_color
        self.pulse_color = pulse_color
        self.pulse_speed = pulse_speed

    def run(self):
        base_rgb = self.lights.COLORS_RGB.get(self.base_color.lower(), (0, 0, 0))
        pulse_rgb = self.lights.COLORS_RGB.get(self.pulse_color.lower(), (0, 0, 0))
        while not self.stop_event.is_set():
            for i in range(0, 100, 5):
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)
                if self.stop_event.wait(self.pulse_speed):
                    return
            for i in range(100, 0, -5):
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)
                if self.stop_event.wait(self.pulse_speed):
                    return