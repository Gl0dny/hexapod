import threading
import abc
from typing import List, Tuple, Dict

class ControlTask(abc.ABC):
    """
    Abstract base class for tasks.

    Attributes:
        thread (threading.Thread): The thread running the task.
        stop_event (threading.Event): Event to signal the task to stop.
    """

    def __init__(self) -> None:
        """
        Initialize the Task object.
        """
        self.thread: threading.Thread = None
        self.stop_event: threading.Event = threading.Event()

    def start(self) -> None:
        """
        Start the task in a separate thread.
        """
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    @abc.abstractmethod
    def run(self) -> None:
        """
        The method to be implemented by subclasses to define the task logic.
        """
        pass

    def stop_task(self) -> None:
        """
        Stop the task and wait for the thread to finish.
        """
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            print(f"Task {self.__class__.__name__} stopping.")
            self.thread.join()

class MonitorCalibrationStatusTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Monitors the calibration status and updates LEDs periodically.
        """
        try:
            while not self.stop_event.is_set():
                updated_status = self.hexapod.calibration.get_calibration_status()
                self.lights_handler.update_calibration_leds_status(updated_status)
                if updated_status and all(status == "calibrated" for status in updated_status.values()):
                    print(updated_status)
                    print("All legs calibrated. Stopping calibration status monitoring.")
                    self.stop_event.set()
                self.stop_event.wait(timeout=0.5)
        except Exception as e:
            print(f"Error in calibration status monitoring thread: {e}")

class RunCalibrationTask(ControlTask):
    def __init__(self, hexapod):
        super().__init__()
        self.hexapod = hexapod

    def run(self) -> None:
        """
        Runs the calibration process.
        """
        self.hexapod.calibrate_all_servos(stop_event=self.stop_event)

class CompositeCalibrationTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.run_calibration_task = RunCalibrationTask(hexapod)
        self.monitor_calibration_task = MonitorCalibrationStatusTask(hexapod, lights_handler)

    def run(self) -> None:
        """
        Starts both RunCalibrationTask and MonitorCalibrationStatusTask.
        """
        self.run_calibration_task.start()
        self.monitor_calibration_task.start()

    def stop_task(self) -> None:
        """
        Stops both RunCalibrationTask and MonitorCalibrationStatusTask.
        """
        self.run_calibration_task.stop_task()
        self.monitor_calibration_task.stop_task()
        super().stop_task()

class HelixTask(ControlTask):
    def __init__(self, hexapod):
        super().__init__()
        self.hexapod = hexapod

        self.helix_positions: Dict[str, List[Tuple[float, float, float]]] = {
            'helix_minimum': [
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_min'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
            ],
            'helix_maximum': [
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
                (self.hexapod.coxa_params['angle_max'], self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_min']),
            ],
        }

    def run(self) -> None:
        """
        Performs a helix maneuver by moving to helix_minimum and then to helix_maximum positions.
        """
        try:
            self.hexapod.move_to_angles_position('helix_minimum', self.helix_positions)
            
            while not self.stop_event.is_set():
                if not self.hexapod.get_moving_state():
                    break
                self.stop_event.wait(timeout=0.1)
            if self.stop_event.is_set():
                return

            self.hexapod.move_to_angles_position('helix_maximum', self.helix_positions)
            
            while not self.stop_event.is_set():
                if not self.hexapod.get_moving_state():
                    break
                self.stop_event.wait(timeout=0.1)

        except Exception as e:
            print(f"Error in HelixTask: {e}")
