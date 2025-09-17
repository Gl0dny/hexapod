import logging
import threading
import abc

from hexapod.lights import Lights
from hexapod.utils import rename_thread

logger = logging.getLogger("lights_logger")


class Animation(threading.Thread, abc.ABC):
    """
    Abstract base class for animations using Lights.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        stop_event (threading.Event): Event to signal the animation to stop.
    """

    def __init__(self, lights: Lights) -> None:
        """
        Initialize the Animation thread and sets up necessary attributes.

        Args:
            lights (Lights): The Lights object to control the LEDs.
        """
        super().__init__(daemon=True)
        rename_thread(self, self.__class__.__name__)

        self.lights: Lights = lights
        self.stop_event: threading.Event = threading.Event()
        logger.debug(f"{self.__class__.__name__} initialized successfully.")

    def start(self) -> None:
        """
        Start the animation in a separate thread.
        Clears the stop event and initiates the thread's run method.
        """
        self.stop_event.clear()
        super().start()

    def run(self):
        """
        Execute the animation.
        """
        self.execute_animation()

    @abc.abstractmethod
    def execute_animation(self) -> None:
        """
        Execute the animation logic.

        This method should be overridden by subclasses to define specific animation behaviors.
        """
        pass

    def stop_animation(self) -> None:
        """
        Signals the animation to stop and joins the thread.

        Sets the stop_event to notify the thread to terminate.
        If the thread is alive, it forcefully stops the thread.
        """
        logger.debug(f"Stopping animation: {self.__class__.__name__}")
        self.stop_event.set()
        if self.is_alive():
            logger.debug(f"Animation {self.__class__.__name__} forcefully stopping.")
            self.join()
