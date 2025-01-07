import threading
import abc
from lights import ColorRGB
import logging

logger = logging.getLogger(__name__)

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
            print(f"Task {self.__class__.__name__} forcefully stopping.")
            self.thread.join()

class EmergencyStopTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Executing emergency stop.")
            # self.hexapod.stop_all_movements()
            self.lights_handler.off()
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")

class WakeUpTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self):
        try:
            self.lights_handler.set_brightness(50)
            self.lights_handler.rainbow()
            self.hexapod.move_to_angles_position("home")
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in Wake up task: {e}")

class SleepTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self):
        try:
            self.lights_handler.set_brightness(5)
            self.lights_handler.set_single_color(ColorRGB.GRAY)
            self.hexapod.wait_until_motion_complete()
            self.hexapod.deactivate_all_servos(self.stop_event)

        except Exception as e:
            print(f"Error in Sleep task: {e}")

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

        finally:
            self.lights_handler.off()

class RunCalibrationTask(ControlTask):
    def __init__(self, hexapod):
        super().__init__()
        self.hexapod = hexapod

    def run(self) -> None:
        """
        Runs the calibration process.
        """
        try:
            self.hexapod.calibrate_all_servos(stop_event=self.stop_event)

        except Exception as e:
            print(f"Error in RunCalibrationTask thread: {e}")
        
        finally:
            self.hexapod.move_to_angles_position('home')

class RunSequenceTask(ControlTask):
    def __init__(self, hexapod, lights_handler, sequence_name):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.sequence_name = sequence_name
        self.sequence_mapping = {
            'startup': [WakeUpTask, MoveTask],
            'shutdown': [StopTask, SleepTask],
            'dance_sequence': [DanceTask, SitUpTask, ShowOffTask],
            # Add more sequences as needed
        }

    def run(self) -> None:
        """
        Executes a predefined sequence of tasks based on the sequence_name.
        """
        try:
            logger.info(f"Starting sequence: {self.sequence_name}")
            tasks = self.sequence_mapping.get(self.sequence_name, [])
            for task_class in tasks:
                if self.stop_event.is_set():
                    logger.info("RunSequenceTask interrupted.")
                    break
                task = task_class(self.hexapod, self.lights_handler)
                task.start()
                task.thread.join()
        except Exception as e:
            logger.error(f"RunSequenceTask '{self.sequence_name}' failed: {e}")
        finally:
            logger.info(f"Sequence '{self.sequence_name}' completed.")
            self.stop_task()
class LowProfileTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Sets the hexapod to a low-profile mode position.
        Positions not defined yet, placeholders only.
        """
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position('low_profile')
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in LowProfileTask: {e}")

        finally:
            self.lights_handler.ready()

class UprightModeTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Sets the hexapod to an upright mode position.
        Positions not defined yet, placeholders only.
        """
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position('upright_mode')
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in UprightModeTask: {e}")
            
        finally:
            self.lights_handler.ready()

class IdleStanceTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Sets the hexapod to the home position.
        """
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position('home')
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in IdleStanceTask: {e}")

        finally:
            self.lights_handler.ready()

class MoveTask(ControlTask):
    def __init__(self, hexapod, direction):
        super().__init__()
        self.hexapod = hexapod
        self.direction = direction

    def run(self) -> None:
        try:
            logger.info(f"Moving {self.direction}.")
            # self.hexapod.move(direction=self.direction)
        except Exception as e:
            logger.error(f"Move task failed: {e}")

class StopTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Executing StopTask: Stopping all ongoing tasks.")
            if self.control_task and self.control_task.is_alive():
                self.control_task.stop_task()
            
            if self.hexapod:
                self.hexapod.deactivate_all_servos()
                logger.info("Hexapod servos deactivated.")
            
            if self.lights_handler:
                self.lights_handler.off()
                logger.info("Lights turned off.")
            
            print("StopTask: All tasks have been stopped.")
        except Exception as e:
            logger.error(f"StopTask failed: {e}")
        finally:
            self.stop_task()
            
class RotateTask(ControlTask):
    def __init__(self, hexapod, angle=None, direction=None):
        super().__init__()
        self.hexapod = hexapod
        self.angle = angle
        self.direction = direction

    def run(self) -> None:
        try:
            if self.angle:
                logger.info(f"Rotating {self.angle} degrees.")
                self.hexapod.rotate(angle=self.angle)
            elif self.direction:
                logger.info(f"Rotating to the {self.direction}.")
                # self.hexapod.rotate(direction=self.direction)
            else:
                logger.error("No angle or direction provided for rotation.")
        except Exception as e:
            logger.error(f"Rotate task failed: {e}")

class FollowTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Starting follow task.")
            # self.hexapod.start_following()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Follow task failed: {e}")

class SoundSourceAnalysisTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Starting sound source analysis.")
            # self.hexapod.analyze_sound_sources()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Sound source analysis task failed: {e}")

class DirectionOfArrivalTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Calculating direction of arrival.")
            # direction = self.hexapod.calculate_direction_of_arrival()
            # logger.info(f"Sound is coming from: {direction}")
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Direction of arrival task failed: {e}")

class SitUpTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Performing sit-up routine.")
            # self.hexapod.perform_sit_up()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Sit-up task failed: {e}")

class DanceTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Starting dance routine.")
            # self.hexapod.perform_dance()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Dance task failed: {e}")

class HelixTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

        helix_min_positions = []
        helix_max_positions = []
        for i in range(6):
            # Read the current angles
            _, femur_angle, tibia_angle = self.hexapod.current_leg_angles[i]
            # Use coxa min or max, keep femur/tibia from the cache
            helix_min_positions.append((self.hexapod.coxa_params['angle_min']+15, femur_angle, tibia_angle))
            helix_max_positions.append((self.hexapod.coxa_params['angle_max'], femur_angle, tibia_angle))

        self.helix_positions = {
            'helix_minimum': helix_min_positions,
            'helix_maximum': helix_max_positions,
        }

    def run(self) -> None:
        """
        Performs a helix maneuver by moving to helix_minimum and then to helix_maximum positions.
        """
        try:
            self.lights_handler.think()
            
            for _ in range(2):
                
                print("Helix maneuver: Moving to 'helix_maximum'")
                self.hexapod.move_to_angles_position('helix_maximum', self.helix_positions)
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return

                print("Helix maneuver: Moving to 'helix_minimum'")
                self.hexapod.move_to_angles_position('helix_minimum', self.helix_positions)
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return
                
            print("Helix maneuver: Finished.")

        except Exception as e:
            print(f"Error in HelixTask: {e}")
            
        finally:
            self.hexapod.move_to_angles_position('home')
            self.lights_handler.ready()
class ShowOffTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Performing show-off routine.")
            # self.hexapod.show_off()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Show-off task failed: {e}")

class SayHelloTask(ControlTask):
    def __init__(self, hexapod, lights_handler):
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        try:
            logger.info("Saying hello.")
            # self.hexapod.say_hello()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Say hello task failed: {e}")