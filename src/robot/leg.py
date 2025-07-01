from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import math
from robot import Joint

if TYPE_CHECKING:
    from typing import Tuple, Dict, Union
    from maestro import MaestroUART

logger = logging.getLogger("robot_logger")

class Leg:
    """
    Initialize a single leg of the hexapod robot.

    The base of the leg is located at the coxa joint. All relative offsets are measured from this base point.

    Attributes:
        coxa_params (dict): Configuration parameters for the coxa joint.
        femur_params (dict): Configuration parameters for the femur joint.
        tibia_params (dict): Configuration parameters for the tibia joint.
        coxa_z_offset (float): Vertical offset of the coxa joint relative to the base.
        tibia_x_offset (float): Horizontal offset of the tibia joint relative to the base.
        coxa (Joint): The coxa joint instance.
        femur (Joint): The femur joint instance.
        tibia (Joint): The tibia joint instance.
        end_effector_offset (tuple): (x, y, z) offset for the end effector's position relative to the leg's base.
        FEMUR_ANGLE_OFFSET (int): 
        TIBIA_ANGLE_OFFSET (int): 
    """
    FEMUR_ANGLE_OFFSET = -90 # Default angle offset for the femur joint in degrees derived from the adopted reference frame.
    TIBIA_ANGLE_OFFSET = -90 # Default angle offset for the tibia joint in degrees derived from the adopted reference frame.

    def __init__(
        self,
        coxa_params: Dict[str, Union[float, bool]],
        femur_params: Dict[str, Union[float, bool]],
        tibia_params: Dict[str, Union[float, bool]],
        controller: MaestroUART,
        end_effector_offset: Tuple[float, float, float]
    ) -> None:
        """
        Initialize a single leg of the hexapod robot.

        Parameters:
            coxa_params (dict): Configuration parameters for the coxa joint, including 'z_offset' to define the vertical offset of the coxa relative to the base.
            femur_params (dict): Configuration parameters for the femur joint.
            tibia_params (dict): Configuration parameters for the tibia joint, including 'x_offset' - horizontal offset of the tibia relative to the base.
            controller (MaestroUART): The shared MaestroUART controller instance for servo communication.
            end_effector_offset (tuple): (x, y, z) offset for the end effector's position relative to the leg's base.
        """
        self.coxa_params = dict(coxa_params)
        self.femur_params = dict(femur_params)
        self.tibia_params = dict(tibia_params)
        
        self.coxa_z_offset = self.coxa_params.pop('z_offset', 0.0)
        self.tibia_x_offset = self.tibia_params.pop('x_offset', 0.0)
        
        self.coxa = Joint(controller, **self.coxa_params)
        self.femur = Joint(controller, **self.femur_params)
        self.tibia = Joint(controller, **self.tibia_params)
        self.end_effector_offset = end_effector_offset

    def _validate_triangle_inequality(self, a: float, b: float, c: float) -> None:
        """
        Validate the triangle inequality for the given side lengths.
        
        Args:
            a (float): Length of side a.
            b (float): Length of side b.
            c (float): Length of side c.
        
        Raises:
            ValueError: If the triangle inequality is not satisfied, with details.
        """
        errors = []
        if a + b <= c:
            errors.append(f"Triangle Inequality Failed: {a} + {b} <= {c} ({a} + {b} = {a + b} <= {c})")
        if a + c <= b:
            errors.append(f"Triangle Inequality Failed: {a} + {c} <= {b} ({a} + {c} = {a + c} <= {b})")
        if b + c <= a:
            errors.append(f"Triangle Inequality Failed: {b} + {c} <= {a} ({b} + {c} = {b + c} <= {a})")
        if errors:
            error_message = "Invalid joint lengths: Triangle inequality not satisfied.\n" + "\n".join(errors)
            logger.error(f"Triangle inequality validation failed with errors: {errors}")
            raise ValueError(error_message)

    def compute_inverse_kinematics(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        Calculate the necessary joint angles to position the foot at the specified coordinates.

        Args:
            x (float): Desired X position of the foot.
            y (float): Desired Y position of the foot.
            z (float): Desired Z position of the foot.

        Returns:
            tuple: A tuple containing the angles for the coxa, femur, and tibia joints in degrees.

        Raises:
            ValueError: If the target position is beyond the leg's maximum reach.
        """
        logger.debug(f"Computing inverse kinematics for position x: {x}, y: {y}, z: {z}")
        # Compensate for end effector offset
        ox, oy, oz = self.end_effector_offset
        x += ox
        y += oy
        z += oz
        logger.debug(f"Adjusted position for IK - x: {x}, y: {y}, z: {z}")

        # Calculate the angle for the coxa joint based on x and y positions
        coxa_angle = math.atan2(x, y)
        logger.debug(f"coxa_angle (radians): {coxa_angle}")

        # Calculate the horizontal distance to the target position
        R = math.hypot(x, y)
        logger.debug(f"R (horizontal_distance): {R}")

        # Distance from femur joint to foot adjusted for coxa length offset
        F = math.hypot(R - self.coxa.length, z - self.coxa_z_offset)
        logger.debug(f"F (distance from femur joint to foot position): {F}")
        
        max_reach = self.femur.length + self.tibia.length
        logger.debug(f"Maximum reach: {max_reach}")
        
        if F > max_reach:
            raise ValueError("Target is out of reach.")

        # Inverse kinematics calculations to find joint angles
        alpha1 = math.atan((R - self.coxa.length) / abs(z - self.coxa_z_offset))
        
        # Replace triangle inequality checks with helper function
        self._validate_triangle_inequality(self.femur.length, self.tibia.length, F)
        
        alpha2 = math.acos((self.tibia.length**2 - self.femur.length**2 - F**2) / (-2 * self.femur.length * F))
       
        logger.debug(f"alpha1 (radians): {alpha1}")
        logger.debug(f"alpha2 (radians): {alpha2}")

        beta = math.acos((F**2 - self.femur.length**2 - self.tibia.length**2) / (-2 * self.femur.length * self.tibia.length))
        logger.debug(f"beta (radians): {beta}")

        coxa_angle_deg = math.degrees(coxa_angle)
        femur_angle_deg = math.degrees(alpha1) + math.degrees(alpha2) + Leg.FEMUR_ANGLE_OFFSET
        tibia_angle_deg = math.degrees(beta) + Leg.TIBIA_ANGLE_OFFSET

        # Round angles to eliminate floating-point precision errors
        coxa_angle_deg = round(coxa_angle_deg, 2)
        femur_angle_deg = round(femur_angle_deg, 2)
        tibia_angle_deg = round(tibia_angle_deg, 2)

        # Normalize -0.0 to 0.0
        coxa_angle_deg = 0.0 if coxa_angle_deg == -0.0 else coxa_angle_deg
        femur_angle_deg = 0.0 if femur_angle_deg == -0.0 else femur_angle_deg
        tibia_angle_deg = 0.0 if tibia_angle_deg == -0.0 else tibia_angle_deg

        logger.debug(f"coxa_angle_deg: {coxa_angle_deg}")
        logger.debug(f"femur_angle_deg: {femur_angle_deg}")
        logger.debug(f"tibia_angle_deg: {tibia_angle_deg}")

        logger.info(f"Calculated angles - coxa_angle_deg: {coxa_angle_deg}, femur_angle_deg: {femur_angle_deg}, tibia_angle_deg: {tibia_angle_deg}")
        return coxa_angle_deg, femur_angle_deg, tibia_angle_deg

    def compute_forward_kinematics(self, coxa_angle_deg: float, femur_angle_deg: float, tibia_angle_deg: float) -> Tuple[float, float, float]:
        """
        Calculate the foot position based on the given joint angles.

        Args:
            coxa_angle_deg (float): Angle of the coxa joint in degrees.
            femur_angle_deg (float): Angle of the femur joint in degrees.
            tibia_angle_deg (float): Angle of the tibia joint in degrees.

        Returns:
            Tuple[float, float, float]: The (x, y, z) coordinates of the foot.
        """
        # Convert angles from degrees to radians for calculations
        coxa_angle = math.radians(coxa_angle_deg)
        femur_angle = math.radians(femur_angle_deg)
        beta_angle_deg = tibia_angle_deg - Leg.TIBIA_ANGLE_OFFSET
        beta = math.radians(beta_angle_deg)

        logger.debug(f"coxa_angle (radians): {coxa_angle}")
        logger.debug(f"femur_angle (radians): {femur_angle}")
        logger.debug(f"beta (radians): {beta_angle_deg}")

        # Calculate the position contributed by the coxa joint
        x_coxa = self.coxa.length * math.sin(coxa_angle)
        y_coxa = self.coxa.length * math.cos(coxa_angle)

        # Calculate vertical displacement from the femur joint
        femur_z = self.femur.length * math.sin(femur_angle)
        # Calculate horizontal distance from the femur joint
        hypotenuse_femur = self.femur.length * math.cos(femur_angle)

        logger.debug(f"x_coxa: {x_coxa}")
        logger.debug(f"y_coxa: {y_coxa}")
        logger.debug(f"femur_z: {femur_z}")
        logger.debug(f"hypotenuse_femur: {hypotenuse_femur}")

        # Calculate the position contributed by the femur joint
        x_femur = hypotenuse_femur * math.sin(coxa_angle)
        y_femur = hypotenuse_femur * math.cos(coxa_angle)

        logger.debug(f"x_femur: {x_femur}")
        logger.debug(f"y_femur: {y_femur}")

        # Compute the distance from femur to tibia using the law of cosines
        F = math.sqrt(self.femur.length**2 + self.tibia.length**2 - 2 * self.femur.length * self.tibia.length * math.cos(beta))
        logger.debug(f"F (distance from femur to end effector): {F}")

        # Replace triangle inequality checks with helper function
        self._validate_triangle_inequality(self.femur.length, self.tibia.length, F)

        # Calculate angle alpha2 using the law of cosines
        alpha2 = math.acos((self.femur.length**2 + F**2 - self.tibia.length**2) / (2 * self.femur.length * F))
        logger.debug(f"alpha2 (radians): {alpha2}")

        # Adjust alpha2 by femur angle to get alpha3
        alpha3 = alpha2 - femur_angle
        logger.debug(f"alpha3 (radians): {alpha3}")

        # Calculate the horizontal and vertical components from femur to tibia
        hypotenuse_femur_tibia = F * math.cos(alpha3)
        tibia_z = F * math.sin(alpha3)

        logger.debug(f"hypotenuse_femur_tibia: {hypotenuse_femur_tibia}")
        logger.debug(f"tibia_z: {tibia_z}")

        # Calculate the position contributed by the tibia joint
        x_tibia = (hypotenuse_femur_tibia - hypotenuse_femur) * math.sin(coxa_angle)
        y_tibia = (hypotenuse_femur_tibia - hypotenuse_femur) * math.cos(coxa_angle)

        logger.debug(f"x_tibia: {x_tibia}")
        logger.debug(f"y_tibia: {y_tibia}")

        # Sum all contributions to get the final foot position
        x = x_coxa + x_femur + x_tibia
        y = y_coxa + y_femur + y_tibia
        z = -tibia_z + self.coxa_z_offset

        # Apply the end effector's offset to the calculated position
        ox, oy, oz = self.end_effector_offset
        x -= ox
        y -= oy
        z -= oz

        # Round the computed positions to eliminate floating-point precision errors
        x = round(x, 2)
        y = round(y, 2)
        z = round(z, 2)

        # Normalize -0.0 to 0.0
        x = 0.0 if x == -0.0 else x
        y = 0.0 if y == -0.0 else y
        z = 0.0 if z == -0.0 else z

        logger.debug(f"Computed forward kinematics - x: {x}, y: {y}, z: {z}")
        return x, y, z

    def _validate_angle(self, joint: Joint, angle: float, check_custom_limits: bool) -> None:
        """
        Validate the angle against both default and custom limits for a given joint.

        Args:
            joint (Joint): The joint to validate.
            angle (float): The angle to validate.
            check_custom_limits (bool): Whether to enforce custom angle limits.

        Raises:
            ValueError: If the angle is outside the allowed limits.
        """
        if not check_custom_limits:
            return

        if not (joint.angle_min <= angle <= joint.angle_max):
            raise ValueError(f"{joint} angle {angle}° is out of bounds ({joint.angle_min}° to {joint.angle_max}°).")
        
        if joint.angle_limit_min is not None and angle < joint.angle_limit_min:
            raise ValueError(f"{joint} angle {angle}° is below custom limit ({joint.angle_limit_min}°).")
        if joint.angle_limit_max is not None and angle > joint.angle_limit_max:
            raise ValueError(f"{joint} angle {angle}° is above custom limit ({joint.angle_limit_max}°).")

    def move_to(
        self,
        x: float,
        y: float,
        z: float,
        check_custom_limits: bool = True
    ) -> None:
        """
        Move the leg's end effector to the specified (x, y, z) coordinates.

        Args:
            x (float): Target X coordinate.
            y (float): Target Y coordinate.
            z (float): Target Z coordinate.
            check_custom_limits (bool, optional): Whether to check custom angle limits. Defaults to True.
        """
        logger.debug(f"Moving to x: {x}, y: {y}, z: {z} with speed/accel set at hexapod level")

        coxa_angle, femur_angle, tibia_angle = self.compute_inverse_kinematics(x, y, z)
        
        # Validate each joint's angle using the helper method
        self._validate_angle(self.coxa, coxa_angle, check_custom_limits)
        self._validate_angle(self.femur, femur_angle, check_custom_limits)
        self._validate_angle(self.tibia, tibia_angle, check_custom_limits)

        self.coxa.set_angle(coxa_angle, check_custom_limits)
        self.femur.set_angle(femur_angle, check_custom_limits)
        self.tibia.set_angle(tibia_angle, check_custom_limits)
        logger.debug(f"Set angles - coxa: {coxa_angle}, femur: {femur_angle}, tibia: {tibia_angle}")

    def move_to_angles(
        self,
        coxa_angle: float,
        femur_angle: float,
        tibia_angle: float,
        check_custom_limits: bool = True
    ) -> None:
        """
        Move the leg's end effector to the specified angles.

        Args:
            coxa_angle (float): Target angle for the coxa joint in degrees.
            femur_angle (float): Target angle for the femur joint in degrees.
            tibia_angle (float): Target angle for the tibia joint in degrees.
            check_custom_limits (bool, optional): Whether to check custom angle limits. Defaults to True.
        """
        # Validate each joint's angle using the helper method
        self._validate_angle(self.coxa, coxa_angle, check_custom_limits)
        self._validate_angle(self.femur, femur_angle, check_custom_limits)
        self._validate_angle(self.tibia, tibia_angle, check_custom_limits)

        self.coxa.set_angle(coxa_angle, check_custom_limits)
        self.femur.set_angle(femur_angle, check_custom_limits)
        self.tibia.set_angle(tibia_angle, check_custom_limits)
        logger.debug(f"Set angles - coxa: {coxa_angle}, femur: {femur_angle}, tibia: {tibia_angle}")