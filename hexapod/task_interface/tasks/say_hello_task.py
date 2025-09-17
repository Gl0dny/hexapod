from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time
import math

from hexapod.task_interface.tasks import Task
from hexapod.robot import PredefinedPosition
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler

logger = get_custom_logger("task_interface_logger")


class SayHelloTask(Task):
    """
    Task for the hexapod to say hello by waving one leg in an infinity sign pattern.
    """

    def __init__(
        self,
        hexapod: Hexapod,
        lights_handler: LightsInteractionHandler,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the SayHelloTask.
        """
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def _perform_infinity_wave(self) -> None:
        """
        Performs the infinity sign wave motion with one leg using angle-based movement.
        The motion creates a figure-8 pattern by varying coxa and femur angles:
        coxa_angle = original_coxa + a * cos(t)
        femur_angle = original_femur + a * sin(t) * cos(t)
        tibia_angle = extended_tibia (kept extended)
        where 'a' controls the size of the infinity sign.
        """
        logger.info("Starting infinity wave motion using angle-based movement")

        # Parameters for the infinity wave - adjusted for joint angle limits
        wave_leg = 0  # Use leg 0 (front right) for waving
        angle_amplitude = 18.0  # Amplitude in degrees for angle variation
        extended_tibia_angle = 45  # Extended tibia angle for better visibility
        cycles = 3  # Number of complete infinity signs to draw
        points_per_cycle = 50  # Number of points to sample per cycle
        total_points = cycles * points_per_cycle

        # Store original angles of the waving leg
        original_coxa, original_femur, original_tibia = self.hexapod.current_leg_angles[
            wave_leg
        ]
        logger.info(
            f"Original leg {wave_leg} angles: coxa={original_coxa:.1f}°, femur={original_femur:.1f}°, tibia={original_tibia:.1f}°"
        )

        # Preparation sequence: Lift leg off the ground
        # Step 1: Move femur to 45 degrees to lift the leg
        self.hexapod.move_leg_angles(wave_leg, original_coxa, 45.0, original_tibia)
        self.hexapod.wait_until_motion_complete(self.stop_event)
        if self.stop_event.is_set():
            logger.info("Infinity wave task interrupted during preparation.")
            return

        # Step 2: Extend the tibia
        self.hexapod.move_leg_angles(
            wave_leg, original_coxa, 45.0, extended_tibia_angle
        )
        self.hexapod.wait_until_motion_complete(self.stop_event)
        if self.stop_event.is_set():
            logger.info("Infinity wave task interrupted during preparation.")
            return

        # Calculate time step for smooth animation
        time_step = 2 * math.pi / points_per_cycle

        for i in range(total_points):
            if self.stop_event.is_set():
                logger.info("Infinity wave task interrupted.")
                return

            # Calculate current angle
            t = i * time_step

            # Parametric equations for infinity sign (figure-8) using joint angles
            # coxa_angle = original_coxa + a * cos(t)
            # femur_angle = original_femur + a * sin(t) * cos(t)
            # tibia_angle = extended_tibia_angle (kept extended)
            delta_coxa = angle_amplitude * math.cos(t)
            delta_femur = angle_amplitude * math.sin(t) * math.cos(t)

            # Calculate new angles relative to original
            new_coxa = original_coxa + delta_coxa
            new_femur = original_femur + delta_femur
            new_tibia = extended_tibia_angle  # Keep tibia extended

            logger.debug(
                f"Moving leg {wave_leg} to angles: coxa={new_coxa:.1f}°, femur={new_femur:.1f}°, tibia={new_tibia:.1f}°"
            )

            # Move the waving leg to the new angles
            self.hexapod.move_leg_angles(wave_leg, new_coxa, new_femur, new_tibia)

            # Interruptible delay for smooth animation
            start_time = time.time()
            while time.time() - start_time < 0.05:  # 50ms delay between points
                if self.stop_event.is_set():
                    logger.info("Infinity wave task interrupted during delay.")
                    return
                time.sleep(0.01)  # Check stop event every 1ms

            # Check stop event during animation
            if self.stop_event.is_set():
                logger.info("Infinity wave task interrupted during animation.")
                return

        # Return the waving leg to its original angles
        logger.info(f"Returning leg {wave_leg} to original angles")
        self.hexapod.move_leg_angles(
            wave_leg, original_coxa, original_femur, original_tibia
        )
        self.hexapod.wait_until_motion_complete(self.stop_event)

    @override
    def execute_task(self) -> None:
        """
        Makes the hexapod say hello by waving one leg in an infinity pattern.
        """
        logger.info("SayHelloTask started")
        try:
            logger.info("Performing hello wave routine.")
            self.lights_handler.think()
            self._perform_infinity_wave()
        except Exception as e:
            logger.exception(f"Say hello task failed: {e}")
        finally:
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.info("SayHelloTask completed")
