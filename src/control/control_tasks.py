import threading
import abc
from lights import ColorRGB
import logging
from typing import Callable, Any, Optional
from robot.hexapod import PredefinedPosition, PredefinedAnglePosition

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
        Initializes the ControlTask with a thread and stop event.
        """
        self.thread: threading.Thread = None
        self.stop_event: threading.Event = threading.Event()

    def start(self) -> None:
        """
        Starts the task in a separate thread.
        """
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    @abc.abstractmethod
    def run(self) -> None:
        """
        The method that contains the task logic to be run.
        """
        pass

    def stop_task(self) -> None:
        """
        Signals the task to stop and joins the thread.
        """
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            logger.info(f"Task {self.__class__.__name__} forcefully stopping.")
            self.thread.join()

class EmergencyStopTask(ControlTask):
    """
    Task to deactivate all servos and turn off lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Deactivates all servos and stops the task.
        """
        try:
            logger.info("Executing emergency stop.")
            self.hexapod.deactivate_all_servos()
            self.lights_handler.off()
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
        finally:
            self.stop_task()

class WakeUpTask(ControlTask):
    """
    Task to wake up the hexapod and set lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Ramps up brightness, plays rainbow effect, and moves to HOME.
        """
        try:
            self.lights_handler.set_brightness(50)
            self.lights_handler.rainbow()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in Wake up task: {e}")
        finally:
            # self.lights_handler.ready()
            pass

class SleepTask(ControlTask):
    """
    Task to reduce brightness, turn lights gray, and deactivate servos.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: Hexapod object to control.
            lights_handler: Handles lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Sets brightness to low, grays out lights, and deactivates servos.
        """
        try:
            self.lights_handler.set_brightness(5)
            self.lights_handler.set_single_color(ColorRGB.GRAY)
            self.hexapod.wait_until_motion_complete()
            self.hexapod.deactivate_all_servos(self.stop_event)

        except Exception as e:
            print(f"Error in Sleep task: {e}")

class CompositeCalibrationTask(ControlTask):
    """
    Orchestrates the execution of run and monitor calibration tasks.
    """
    def __init__(self, hexapod: Any, lights_handler: Any, control_interface: Any) -> None:
        """
        Args:
            hexapod: Hexapod object to calibrate.
            lights_handler: Handles lights display during calibration.
            control_interface: The control interface instance used for managing maintenance mode event.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.control_interface = control_interface
        self.run_calibration_task = RunCalibrationTask(hexapod)
        self.monitor_calibration_task = MonitorCalibrationStatusTask(hexapod, lights_handler)

    def run(self) -> None:
        """
        Starts RunCalibrationTask and MonitorCalibrationStatusTask.
        """
        try:
            logger.info("Starting composite calibration task.")
            self.run_calibration_task.start()
            self.monitor_calibration_task.start()
            self.run_calibration_task.thread.join()
            self.monitor_calibration_task.thread.join()
        except Exception as e:
            logger.error(f"Composite calibration task failed: {e}")
        finally:
            self.control_interface.maintenance_mode_event.clear()
            logger.info("Composite calibration task completed.")

    def stop_task(self) -> None:
        """
        Stops RunCalibrationTask and MonitorCalibrationStatusTask.
        """
        self.run_calibration_task.stop_task()
        self.monitor_calibration_task.stop_task()
        super().stop_task()

class MonitorCalibrationStatusTask(ControlTask):
    """
    Continuously monitors calibration status and updates lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: Hexapod under calibration.
            lights_handler: Manages the calibration LED status.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Checks if all legs are calibrated and stops if so.
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
    """
    Runs the calibration routine for all servos.
    """
    def __init__(self, hexapod: Any) -> None:
        """
        Args:
            hexapod: Hexapod whose servos are being calibrated.
        """
        super().__init__()
        self.hexapod = hexapod

    def run(self) -> None:
        """
        Calibrates all servos and moves to 'home' upon completion.
        """
        try:
            self.hexapod.calibrate_all_servos(stop_event=self.stop_event)

        except Exception as e:
            print(f"Error in RunCalibrationTask thread: {e}")
        
        finally:
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

class RunSequenceTask(ControlTask):
    """
    Executes a predefined sequence of tasks.
    """
    def __init__(self, hexapod: Any, lights_handler: Any, sequence_name: str) -> None:
        """
        Args:
            hexapod: Hexapod object to control.
            lights_handler: Handles lights activity.
            sequence_name: Name of the sequence to run.
        """
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
        Runs the tasks associated with the selected sequence.
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
    """
    Task to set the hexapod to a low-profile mode and manage related lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
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
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in LowProfileTask: {e}")

        finally:
            self.lights_handler.ready()

class UprightModeTask(ControlTask):
    """
    Task to set the hexapod to an upright mode and manage related lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
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
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.UPRIGHT_MODE)
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in UprightModeTask: {e}")
            
        finally:
            self.lights_handler.ready()

class IdleStanceTask(ControlTask):
    """
    Task to set the hexapod to the home position and manage related lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Sets the hexapod to the home position.
        """
        try:
            self.lights_handler.think()
            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(self.stop_event)

        except Exception as e:
            print(f"Error in IdleStanceTask: {e}")

        finally:
            self.lights_handler.ready()

class MoveTask(ControlTask):
    """
    Task to move the hexapod in a specified direction.
    """
    def __init__(self, hexapod: Any, direction: str) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            direction: Direction to move the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.direction = direction

    def run(self) -> None:
        """
        Moves the hexapod in the specified direction.
        """
        try:
            logger.info(f"Moving {self.direction}.")
            # self.hexapod.move(direction=self.direction)
        except Exception as e:
            logger.error(f"Move task failed: {e}")

class StopTask(ControlTask):
    """
    Task to stop all ongoing tasks and deactivate the hexapod.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Stops all ongoing tasks, deactivates servos, and turns off lights.
        """
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
    """
    Task to rotate the hexapod by a certain angle or direction.
    """
    def __init__(self, hexapod: Any, angle: Optional[float] = None, direction: Optional[str] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            angle: Angle in degrees to rotate.
            direction: Direction to rotate the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.angle = angle
        self.direction = direction

    def run(self) -> None:
        """
        Rotates the hexapod based on the provided angle or direction.
        """
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
    """
    Task to make the hexapod follow a target and manage related lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Starts following a target and manages lights accordingly.
        """
        try:
            logger.info("Starting follow task.")
            # self.hexapod.start_following()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Follow task failed: {e}")

class SoundSourceAnalysisTask(ControlTask):
    """
    Task to analyze sound sources and manage related lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Analyzes sound sources and updates lights accordingly.
        """
        try:
            logger.info("Starting sound source analysis.")
            # self.hexapod.analyze_sound_sources()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Sound source analysis task failed: {e}")

class DirectionOfArrivalTask(ControlTask):
    """
    Task to calculate the direction of arrival of sounds and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Calculates the direction of arrival of sounds and updates lights.
        """
        try:
            logger.info("Calculating direction of arrival.")
            # direction = self.hexapod.calculate_direction_of_arrival()
            # logger.info(f"Sound is coming from: {direction}")
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Direction of arrival task failed: {e}")

class SitUpTask(ControlTask):
    """
    Task to perform sit-up routine with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Performs the sit-up routine.
        """
        try:
            logger.info("Performing sit-up routine.")
            # self.hexapod.perform_sit_up()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Sit-up task failed: {e}")

class DanceTask(ControlTask):
    """
    Task to perform dance routine with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Performs the dance routine.
        """
        try:
            logger.info("Starting dance routine.")
            # self.hexapod.perform_dance()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Dance task failed: {e}")

class HelixTask(ControlTask):
    """
    Task to perform a helix maneuver with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

        helix_min_positions = []
        helix_max_positions = []
        for i in range(6):
            # Read the current angles
            _, femur_angle, tibia_angle = self.hexapod.current_leg_angles[i]
            # Use coxa min or max, keep femur/tibia from the cache
            helix_min_positions.append((self.hexapod.coxa_params['angle_min']+25, femur_angle, tibia_angle))
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
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_maximum'])
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return

                print("Helix maneuver: Moving to 'helix_minimum'")
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_minimum'])
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return
                
            print("Helix maneuver: Finished.")

        except Exception as e:
            print(f"Error in HelixTask: {e}")
            
        finally:
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.lights_handler.ready()

class ShowOffTask(ControlTask):
    """
    Task to perform show-off routine with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Performs the show-off routine.
        """
        try:
            logger.info("Performing show-off routine.")
            # self.hexapod.show_off()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Show-off task failed: {e}")

class SayHelloTask(ControlTask):
    """
    Task for the hexapod to say hello and manage lights.
    """
    def __init__(self, hexapod: Any, lights_handler: Any) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
        """
        super().__init__()
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def run(self) -> None:
        """
        Makes the hexapod say hello.
        """
        try:
            logger.info("Saying hello.")
            # self.hexapod.say_hello()
            self.lights_handler.ready()
        except Exception as e:
            logger.error(f"Say hello task failed: {e}")