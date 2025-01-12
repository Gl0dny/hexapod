import threading
import abc
from lights import ColorRGB, LightsInteractionHandler
import logging
from typing import Optional, Callable, override
from robot.hexapod import PredefinedPosition, PredefinedAnglePosition, Hexapod
from utils import rename_thread

logger = logging.getLogger("control_logger")

class ControlTask(threading.Thread, abc.ABC):
    """
    Abstract base class for control tasks executed by the hexapod.

    Attributes:
        stop_event (threading.Event): Event to signal the task to stop.
        callback (Optional[Callable]): Function to call upon task completion.
    """

    def __init__(self, callback: Optional[Callable] = None) -> None:
        """
        Initializes the ControlTask with threading.Thread.

        Args:
            callback (Optional[Callable]): Function to execute after task completion.
        """
        super().__init__(daemon=True)
        rename_thread(self, self.__class__.__name__)

        self.stop_event: threading.Event = threading.Event()
        self.callback = callback
        logger.debug(f"{self.__class__.__name__} initialized successfully.")

    def start(self) -> None:
        """
        Start the control task in a separate thread.

        Clears the stop event and initiates the thread's run method.
        """
        logger.debug(f"Starting task: {self.__class__.__name__}")
        self.stop_event.clear()
        super().start()

    def run(self) -> None:
        """
        Execute the task and invoke the callback upon completion.
        """
        logger.debug(f"Running task: {self.__class__.__name__}")
        self.execute_task()
        if self.callback:
            self.callback()

    @abc.abstractmethod
    def execute_task(self) -> None:
        """
        Execute the task and invoke the callback upon completion.

        This method should be overridden by subclasses to define specific task behaviors.
        """
        pass

    def stop_task(self) -> None:
        """
        Signals the task to stop and joins the thread.

        Sets the stop_event to notify the thread to terminate.
        If the thread is alive, it forcefully stops the thread and invokes the callback if provided.
        """
        logger.info(f"Stopping task: {self.__class__.__name__}")
        self.stop_event.set()
        if self.is_alive():
            logger.info(f"Task {self.__class__.__name__} forcefully stopping.")
            self.join()

class EmergencyStopTask(ControlTask):
    """
    Task to perform an emergency stop, deactivating all servos and turning off lights.

    This task ensures that the hexapod halts all activities immediately for safety.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the EmergencyStopTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing EmergencyStopTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Deactivate all servos and turn off lights to perform an emergency stop.
        """
        logger.info("EmergencyStopTask started")
        try:
            logger.info("Executing emergency stop.")
            self.hexapod.deactivate_all_servos()
            logger.debug("All servos deactivated")
            self.lights_handler.off()
            logger.debug("All lights turned off")
        except Exception as e:
            logger.exception(f"Emergency stop failed: {e}")
        finally:
            logger.info("EmergencyStopTask completed")
            self.stop_task()

class WakeUpTask(ControlTask):
    """
    Task to wake up the hexapod, adjust lighting, and move to the HOME position.

    This task ramps up brightness, plays a rainbow lighting effect, and moves the hexapod to its home position.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the WakeUpTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing WakeUpTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Ramp up brightness, activate rainbow lighting, and move the hexapod to the HOME position.
        """
        logger.info("WakeUpTask started")
        try:
            self.lights_handler.set_brightness(50)
            self.lights_handler.rainbow()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod woke up")

        except Exception as e:
            logger.exception(f"Error in Wake up task: {e}")
        finally:
            logger.info("WakeUpTask completed")

class SleepTask(ControlTask):
    """
    Task to put the hexapod into sleep mode by reducing brightness, graying out lights, and deactivating servos.

    This task ensures the hexapod conserves energy and enters a low-power state.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SleepTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing SleepTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Reduce brightness, set lights to gray, and deactivate all servos to enter sleep mode.
        """
        logger.info("SleepTask started")
        try:
            self.lights_handler.set_brightness(5)
            self.lights_handler.set_single_color(ColorRGB.GRAY)
            self.hexapod.wait_until_motion_complete()
            self.hexapod.deactivate_all_servos(self.stop_event)
            logger.debug("Hexapod is now sleeping")

        except Exception as e:
            logger.exception(f"Error in Sleep task: {e}")
        finally:
            logger.info("SleepTask completed")

class CompositeCalibrationTask(ControlTask):
    """
    Task to orchestrate the calibration process by running and monitoring calibration tasks.

    This composite task manages both the execution of calibration routines and the monitoring of their status.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, maintenance_mode_event: threading.Event, callback: Optional[Callable] = None) -> None:
        """
        Initialize the CompositeCalibrationTask.

        Args:
            hexapod (Hexapod): The hexapod instance to calibrate.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights during calibration.
            maintenance_mode_event (threading.Event): Event to manage maintenance mode state.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing CompositeCalibrationTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.maintenance_mode_event = maintenance_mode_event
        self.run_calibration_task = RunCalibrationTask(hexapod)
        self.monitor_calibration_task = MonitorCalibrationStatusTask(hexapod, lights_handler)

    @override
    def execute_task(self) -> None:
        """
        Start and manage the RunCalibrationTask and MonitorCalibrationStatusTask.

        Initiates both calibration and monitoring tasks, ensuring they run concurrently.
        """
        logger.info("CompositeCalibrationTask started")
        try:
            logger.user_info("Starting composite calibration task.")
            self.monitor_calibration_task.start()
            self.run_calibration_task.start()
            self.run_calibration_task.join()
            self.monitor_calibration_task.join()
            logger.debug("Composite calibration completed")
        except Exception as e:
            logger.exception(f"Composite calibration task failed: {e}")
        finally:
            self.maintenance_mode_event.clear()
            logger.info("CompositeCalibrationTask completed.")

    @override
    def stop_task(self) -> None:
        """
        Stop both the RunCalibrationTask and MonitorCalibrationStatusTask, then perform superclass cleanup.

        Ensures that both calibration and monitoring tasks are properly terminated before cleaning up.
        """
        self.run_calibration_task.stop_task()
        self.monitor_calibration_task.stop_task()
        super().stop_task()

class MonitorCalibrationStatusTask(ControlTask):
    """
    Continuously monitors calibration status and updates lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: Hexapod under calibration.
            lights_handler: Manages the calibration LED status.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MonitorCalibrationStatusTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Checks if all legs are calibrated and stops if so.
        """
        logger.user_info("MonitorCalibrationStatusTask started")
        try:
            updated_status = self.hexapod.calibration.get_calibration_status()
            self.lights_handler.update_calibration_leds_status(calibration_status=updated_status)
            while not self.stop_event.is_set():
                logger.debug(f"Calibration status: {updated_status}")
                if updated_status and all(status == "calibrated" for status in updated_status.values()):
                    logger.user_info("All legs calibrated. Stopping calibration status monitoring.")
                    self.stop_event.set()
                self.stop_event.wait(timeout=5)
                
        except Exception as e:
            logger.exception(f"Error in calibration status monitoring thread: {e}")

        finally:
            logger.info("MonitorCalibrationStatusTask completed")
            self.lights_handler.off()

class RunCalibrationTask(ControlTask):
    """
    Runs the calibration routine for all servos.
    """
    def __init__(self, hexapod: Hexapod, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: Hexapod whose servos are being calibrated.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RunCalibrationTask")
        super().__init__(callback)
        self.hexapod = hexapod

    @override
    def execute_task(self) -> None:
        """
        Calibrates all servos and moves to 'home' upon completion.
        """
        logger.user_info("RunCalibrationTask started")
        try:
            self.hexapod.calibrate_all_servos(stop_event=self.stop_event)

        except Exception as e:
            logger.exception(f"Error in RunCalibrationTask thread: {e}")
        
        finally:
            logger.info("RunCalibrationTask completed")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

class RunSequenceTask(ControlTask):
    """
    Executes a predefined sequence of tasks.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, sequence_name: str, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: Hexapod object to control.
            lights_handler: Handles lights activity.
            sequence_name: Name of the sequence to run.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RunSequenceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.sequence_name = sequence_name
        self.sequence_mapping = {
            'startup': [WakeUpTask, MoveTask],
            'shutdown': [StopTask, SleepTask],
            'dance_sequence': [DanceTask, SitUpTask, ShowOffTask],
            # Add more sequences as needed
        }

    @override
    def execute_task(self) -> None:
        """
        Runs the tasks associated with the selected sequence.
        """
        logger.info(f"RunSequenceTask started: {self.sequence_name}")
        try:
            logger.info(f"Starting sequence: {self.sequence_name}")
            tasks = self.sequence_mapping.get(self.sequence_name, [])
            for task_class in tasks:
                if self.stop_event.is_set():
                    logger.info("RunSequenceTask interrupted.")
                    break
                task = task_class(self.hexapod, self.lights_handler)
                task.start()
                task.join()
        except Exception as e:
            logger.exception(f"RunSequenceTask '{self.sequence_name}' failed: {e}")
        finally:
            logger.info(f"Sequence '{self.sequence_name}' completed.")
            self.stop_task()

class LowProfileTask(ControlTask):
    """
    Task to set the hexapod to a low-profile mode and manage related lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing LowProfileTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Sets the hexapod to a low-profile mode position.
        Positions not defined yet, placeholders only.
        """
        logger.info("LowProfileTask started")
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod set to low-profile mode")

        except Exception as e:
            logger.exception(f"Error in LowProfileTask: {e}")

        finally:
            logger.info("LowProfileTask completed")

class UprightModeTask(ControlTask):
    """
    Task to set the hexapod to an upright mode and manage related lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing UprightModeTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Sets the hexapod to an upright mode position.
        Positions not defined yet, placeholders only.
        """
        logger.info("UprightModeTask started")
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.UPRIGHT_MODE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod set to upright mode")

        except Exception as e:
            logger.exception(f"Error in UprightModeTask: {e}")
            
        finally:
            logger.info("UprightModeTask completed")

class IdleStanceTask(ControlTask):
    """
    Task to set the hexapod to the home position and manage related lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing IdleStanceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Sets the hexapod to the home position.
        """
        logger.info("IdleStanceTask started")
        try:
            self.lights_handler.think()
            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod set to home position")

        except Exception as e:
            logger.exception(f"Error in IdleStanceTask: {e}")

        finally:
            logger.info("IdleStanceTask completed")

class MoveTask(ControlTask):
    """
    Task to move the hexapod in a specified direction.
    """
    def __init__(self, hexapod: Hexapod, direction: str, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            direction: Direction to move the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MoveTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.direction = direction

    @override
    def execute_task(self) -> None:
        """
        Moves the hexapod in the specified direction.
        """
        logger.info("MoveTask started")
        try:
            logger.info(f"Moving {self.direction}.")
            # self.hexapod.move(direction=self.direction)
        except Exception as e:
            logger.exception(f"Move task failed: {e}")
        finally:
            logger.info("MoveTask completed")

class StopTask(ControlTask):
    """
    Task to stop all ongoing tasks and deactivate the hexapod.

    This task ensures that all active tasks are halted and the hexapod is safely deactivated.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the StopTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing StopTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Stops all ongoing tasks, deactivates servos, and turns off lights.

        This method ensures that the hexapod stops all activities and enters a safe state.
        """
        logger.info("StopTask started")
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
            logger.exception(f"StopTask failed: {e}")
        finally:
            logger.info("StopTask completed")
            self.stop_task()
            
class RotateTask(ControlTask):
    """
    Task to rotate the hexapod by a certain angle or direction.

    Allows the hexapod to rotate either by a specified angle in degrees or towards a cardinal direction.
    """
    def __init__(self, hexapod: Hexapod, angle: Optional[float] = None, direction: Optional[str] = None, callback: Optional[Callable] = None) -> None:
        """
        Initialize the RotateTask.

        Args:
            hexapod: The hexapod object to control.
            angle: Angle in degrees to rotate.
            direction: Direction to rotate the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RotateTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.angle = angle
        self.direction = direction

    @override
    def execute_task(self) -> None:
        """
        Rotates the hexapod based on the provided angle or direction.

        Executes rotation either by a specified angle or towards a specified direction.
        """
        logger.info("RotateTask started")
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
            logger.exception(f"Rotate task failed: {e}")
        finally:
            logger.info("RotateTask completed")

class FollowTask(ControlTask):
    """
    Task to make the hexapod follow a target and manage related lights.

    Enables the hexapod to track and follow a designated target while updating light indicators.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the FollowTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing FollowTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Starts following a target and manages lights accordingly.

        Initiates the tracking of a target and updates light indicators based on the target's movement.
        """
        logger.info("FollowTask started")
        try:
            logger.info("Starting follow task.")
            # self.hexapod.start_following()
        except Exception as e:
            logger.exception(f"Follow task failed: {e}")
        finally:
            logger.info("FollowTask completed")

class SoundSourceAnalysisTask(ControlTask):
    """
    Task to analyze sound sources and manage related lights.

    Processes incoming sound data to determine source directions and updates lights based on analysis.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SoundSourceAnalysisTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SoundSourceAnalysisTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Analyzes sound sources and updates lights accordingly.

        Processes sound input to identify directions of incoming sounds and adjusts lights to indicate sources.
        """
        logger.info("SoundSourceAnalysisTask started")
        try:
            logger.info("Starting sound source analysis.")
            # self.hexapod.analyze_sound_sources()
        except Exception as e:
            logger.exception(f"Sound source analysis task failed: {e}")
        finally:
            logger.info("SoundSourceAnalysisTask completed")

class DirectionOfArrivalTask(ControlTask):
    """
    Task to calculate the direction of arrival of sounds and manage lights.

    Determines the direction from which a sound originates and updates visual indicators accordingly.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the DirectionOfArrivalTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing DirectionOfArrivalTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Calculates the direction of arrival of sounds and updates lights.

        Uses sound analysis to determine the origin direction and updates light indicators to reflect this information.
        """
        logger.info("DirectionOfArrivalTask started")
        try:
            logger.info("Calculating direction of arrival.")
            # direction = self.hexapod.calculate_direction_of_arrival()
            # logger.info(f"Sound is coming from: {direction}")
        except Exception as e:
            logger.exception(f"Direction of arrival task failed: {e}")
        finally:
            logger.info("DirectionOfArrivalTask completed")

class SitUpTask(ControlTask):
    """
    Task to perform sit-up routine with the hexapod and manage lights.

    Executes a series of movements to simulate a sit-up motion while maintaining light activity.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SitUpTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SitUpTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the sit-up routine.

        Executes the predefined sit-up movements and updates lights to indicate activity.
        """
        logger.info("SitUpTask started")
        try:
            logger.info("Performing sit-up routine.")
            # self.hexapod.perform_sit_up()
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")
        finally:
            logger.info("SitUpTask completed")

class DanceTask(ControlTask):
    """
    Task to perform dance routine with the hexapod and manage lights.

    Coordinates a sequence of movements to perform a dance routine, syncing with light patterns.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the DanceTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing DanceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the dance routine.

        Executes a series of dance moves and updates lights to enhance visual effects.
        """
        logger.info("DanceTask started")
        try:
            logger.info("Starting dance routine.")
            # self.hexapod.perform_dance()
        except Exception as e:
            logger.exception(f"Dance task failed: {e}")
        finally:
            logger.info("DanceTask completed")

class HelixTask(ControlTask):
    """
    Task to perform a helix maneuver with the hexapod and manage lights.

    Executes a helix-like movement pattern by alternating between minimum and maximum positions.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the HelixTask.

        Args:
            hexapod (Hexapod): The hexapod object to control.
            lights_handler (LightsInteractionHandler): Manages lights on the hexapod.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        super().__init__(callback)
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

    @override
    def execute_task(self) -> None:
        """
        Performs a helix maneuver by moving to helix_minimum and then to helix_maximum positions.

        Repeats the maneuver twice to complete the helix pattern.
        """
        try:
            self.lights_handler.think()
            
            for _ in range(2):
                
                logger.debug("Helix maneuver: Moving to 'helix_maximum'")
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_maximum'])
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return

                logger.debug("Helix maneuver: Moving to 'helix_minimum'")
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_minimum'])
                
                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return
                
            logger.debug("Helix maneuver: Finished.")

        except Exception as e:
            logger.exception(f"Error in HelixTask: {e}")
            
        finally:
            logger.info("HelixTask completed")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

class ShowOffTask(ControlTask):
    """
    Task to perform show-off routine with the hexapod and manage lights.

    Engages the hexapod in a show-off sequence, showcasing its capabilities with coordinated movements and lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the ShowOffTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing ShowOffTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the show-off routine.

        Executes advanced movements and light patterns to demonstrate the hexapod's features.
        """
        logger.info("ShowOffTask started")
        try:
            logger.info("Performing show-off routine.")
            # self.hexapod.show_off()
        except Exception as e:
            logger.exception(f"Show-off task failed: {e}")
        finally:
            logger.info("ShowOffTask completed")

class SayHelloTask(ControlTask):
    """
    Task for the hexapod to say hello and manage lights.

    Enables the hexapod to perform a greeting action accompanied by light indicators.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SayHelloTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SayHelloTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Makes the hexapod say hello.

        Triggers the greeting action and updates lights to reflect the interaction.
        """
        logger.info("SayHelloTask started")
        try:
            logger.info("Saying hello.")
            # self.hexapod.say_hello()
        except Exception as e:
            logger.exception(f"Say hello task failed: {e}")
        finally:
            logger.info("SayHelloTask completed")