from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import threading

from hexapod.task_interface.tasks import Task
from hexapod.robot import PredefinedPosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler

logger = logging.getLogger("task_interface_logger")

class CompositeCalibrationTask(Task):
    """
    Task to orchestrate the calibration process by running and monitoring calibration tasks.

    This composite task manages both the execution of calibration routines and the monitoring of their status.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, external_control_paused_event: threading.Event, callback: Optional[Callable] = None) -> None:
        """
        Initialize the CompositeCalibrationTask.

        Args:
            hexapod (Hexapod): The hexapod instance to calibrate.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights during calibration.
            external_control_paused_event (threading.Event): Event to manage external control state.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.external_control_paused_event = external_control_paused_event
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
            # Clear external control paused to resume voice control
            self.external_control_paused_event.clear()
            logger.info("CompositeCalibrationTask completed")

    @override
    def stop_task(self, timeout: Optional[float] = None) -> None:
        """
        Stop both the RunCalibrationTask and MonitorCalibrationStatusTask, then perform superclass cleanup.

        Args:
            timeout (Optional[float]): Maximum time to wait for tasks to stop in seconds.
                                     If None, wait indefinitely.

        Ensures that both calibration and monitoring tasks are properly terminated before cleaning up.
        """
        logger.info("Stopping composite calibration task")
        try:
            # Stop child tasks
            self.run_calibration_task.stop_task()
            self.monitor_calibration_task.stop_task()

            # Wait for tasks to complete if timeout is specified
            if timeout is not None:
                self.run_calibration_task.join(timeout=timeout)
                self.monitor_calibration_task.join(timeout=timeout)
            else:
                self.run_calibration_task.join()
                self.monitor_calibration_task.join()

            # Perform superclass cleanup
            super().stop_task()
        except Exception as e:
            logger.exception(f"Error stopping composite calibration task: {e}")
            raise

class MonitorCalibrationStatusTask(Task):
    """
    Continuously monitors calibration status and updates lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod (Hexapod): Hexapod under calibration.
            lights_handler (LightsInteractionHandler): Manages the calibration LED status.
            callback (Optional[Callable]): Function to call upon task completion.
        """
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Checks if all legs are calibrated and stops if so.
        """
        logger.info("MonitorCalibrationStatusTask started")
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

class RunCalibrationTask(Task):
    """
    Runs the calibration routine for all servos.
    """
    def __init__(self, hexapod: Hexapod, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod (Hexapod): Hexapod whose servos are being calibrated.
            callback (Optional[Callable]): Function to call upon task completion.
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
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(stop_event=self.stop_event)