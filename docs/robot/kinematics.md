# Kinematics

[← Previous: Movement System](movement_system.md) | [Next: Gait System →](gait_system.md)

[← Back to Documentation](../README.md)

## Table of Contents

- [Overview](#overview)
- [Leg Structure](#leg-structure)
- [Coordinate System](#coordinate-system)
- [Inverse Kinematics Implementation](#inverse-kinematics-implementation)
- [Body Kinematics](#body-kinematics)
- [Joint Management](#joint-management)
- [Performance Characteristics](#performance-characteristics)

---

## Overview

The kinematics system implements inverse kinematics calculations that convert desired foot positions into the exact servo angles needed to achieve them. The system uses geometric inverse kinematics with triangle relationships to calculate joint angles for the 3-degree-of-freedom legs.

## Leg Structure

### Physical Configuration

Each leg has 3 degrees of freedom with specific dimensions:

```mermaid
graph TD
    subgraph "Leg Structure"
        FP[Foot Position<br/>(x, y, z)]
        T[Tibia<br/>140.0mm<br/>Pitch Servo]
        F[Femur<br/>52.5mm<br/>Pitch Servo]
        C[Coxa<br/>27.5mm<br/>Yaw Servo]
        BM[Body Mount]
    end
    
    FP --> T
    T --> F
    F --> C
    C --> BM
```

### Leg Dimensions

- **Coxa Length**: 27.5mm (horizontal rotation)
- **Femur Length**: 52.5mm (vertical rotation)
- **Tibia Length**: 140.0mm (vertical rotation)
- **End Effector Offset**: (22.5, 80.0, -162.5) mm

### Joint Parameters

- **Coxa Joint**: -45° to +45° range, Z-offset: -22.5mm
- **Femur Joint**: -45° to +45° range, inverted servo
- **Tibia Joint**: -45° to +45° range, X-offset: 22.5mm, custom limits: -35° to +45°

## Coordinate System

### Robot Frame (Right-Handed)

- **+X**: Points to the robot's RIGHT side
- **+Y**: Points FORWARD (in front of the robot)
- **+Z**: Points UP

### Leg Frame

Each leg uses a local coordinate system:
- **X-axis**: Forward direction (positive = forward)
- **Y-axis**: Left direction (positive = left)
- **Z-axis**: Up direction (positive = up)

## Inverse Kinematics Implementation

### Core Algorithm

The inverse kinematics uses geometric triangle relationships to calculate joint angles:

```python
def compute_inverse_kinematics(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    Calculate the necessary joint angles to position the foot at the specified coordinates.
    
    Args:
        x (float): Desired X position of the foot
        y (float): Desired Y position of the foot
        z (float): Desired Z position of the foot
    
    Returns:
        tuple: (coxa_angle, femur_angle, tibia_angle) in degrees
    """
    # Compensate for end effector offset
    ox, oy, oz = self.end_effector_offset
    x += ox
    y += oy
    z += oz
    
    # Calculate coxa angle (horizontal rotation)
    coxa_angle = math.atan2(x, y)
    
    # Calculate horizontal distance to target
    R = math.hypot(x, y)
    
    # Distance from femur joint to foot
    F = math.hypot(R - self.coxa.length, z - self.coxa_z_offset)
    
    # Validate reachability
    max_reach = self.femur.length + self.tibia.length
    if F > max_reach:
        raise ValueError("Target is out of reach.")
    
    # Triangle inequality validation
    self._validate_triangle_inequality(self.femur.length, self.tibia.length, F)
    
    # Calculate joint angles using geometric relationships
    alpha1 = math.atan((R - self.coxa.length) / abs(z - self.coxa_z_offset))
    alpha2 = math.acos((self.tibia.length**2 - self.femur.length**2 - F**2) / 
                      (-2 * self.femur.length * F))
    beta = math.acos((F**2 - self.femur.length**2 - self.tibia.length**2) / 
                    (-2 * self.femur.length * self.tibia.length))
    
    # Convert to degrees and apply offsets
    coxa_angle_deg = math.degrees(coxa_angle)
    femur_angle_deg = math.degrees(alpha1) + math.degrees(alpha2) + Leg.FEMUR_ANGLE_OFFSET
    tibia_angle_deg = math.degrees(beta) + Leg.TIBIA_ANGLE_OFFSET
    
    return coxa_angle_deg, femur_angle_deg, tibia_angle_deg
```

### Mathematical Foundation

1. **Coxa Angle**: `atan2(x, y)` for horizontal positioning
2. **Horizontal Distance**: `sqrt(x² + y²)` for projection
3. **Triangle Validation**: Ensures target is reachable
4. **Geometric Relationships**: Uses cosine law for angle calculations

### Reachability Validation

The system validates that target positions are within the leg's reach:

- **Maximum Reach**: `femur_length + tibia_length = 192.5mm`
- **Triangle Inequality**: Ensures valid triangle formation
- **Error Handling**: Raises `ValueError` for unreachable positions

## Body Kinematics

### Body Movement Calculation

The system implements body inverse kinematics for coordinated movement:

```python
def _compute_body_inverse_kinematics(self, tx: float, ty: float, tz: float, 
                                   roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Compute how far each foot must move in body coordinates so that the
    feet remain fixed in the world while the body undergoes the commanded
    translation and rotation.
    """
    # Initial nominal foot positions in the body frame
    initial_positions = np.array([
        [self.end_effector_radius * np.cos(th),
         self.end_effector_radius * np.sin(th),
         -self.tibia_params["length"]]
        for th in self.leg_angles
    ])
    
    # Build BODY→WORLD transform
    Tb_w = homogeneous_transformation_matrix(
        -tx, -ty, -tz,          # inverse translation
        pitch, -roll, yaw        # swapped arguments, negated roll
    )
    
    # Apply transformation
    homogenous_pos = np.hstack((initial_positions, np.ones((6, 1))))
    transformed = (homogenous_pos @ Tb_w.T)[:, :3]
    
    # Calculate deltas relative to initial positions
    deltas = transformed - initial_positions
    return deltas
```

### Coordinate Transformations

- **Body Frame**: Robot-centered coordinate system
- **Leg Frames**: Individual leg coordinate systems
- **World Frame**: Global reference frame
- **Homogeneous Transforms**: Matrix-based transformations

## Joint Management

### Joint Class

Each joint is managed by the `Joint` class:

```python
class Joint:
    def __init__(self, channel: int, servo_min: int, servo_max: int, 
                 angle_min: float, angle_max: float, invert: bool = False):
        self.channel = channel
        self.servo_min = servo_min
        self.servo_max = servo_max
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.invert = invert
    
    def set_angle(self, angle: float, check_custom_limits: bool = True):
        """Set the joint to a specific angle"""
        if self.invert:
            angle = -angle
        
        self._validate_angle(angle, check_custom_limits)
        target = self.angle_to_servo_target(angle)
        self.controller.set_target(self.channel, target)
```

### Angle Validation

- **Hardware Limits**: Servo-specific angle ranges
- **Custom Limits**: Additional safety constraints
- **Inversion**: Servo direction correction
- **Range Mapping**: Angle to servo target conversion

### Servo Calibration

Each servo has individual calibration values:

- **Servo Min/Max**: Quarter-microsecond pulse widths
- **Angle Mapping**: Linear mapping from angles to servo targets
- **Calibration Data**: Stored in `calibration.json` per leg

## Performance Characteristics

### Calculation Performance

- **Real-time Processing**: 50Hz update rate
- **Computational Efficiency**: Geometric calculations
- **Memory Usage**: Minimal overhead
- **Precision**: 2 decimal places for angles

### Accuracy

- **Position Accuracy**: ±2mm for foot positioning
- **Angle Precision**: 0.01° resolution
- **Repeatability**: Consistent results across calculations
- **Error Handling**: Graceful failure for unreachable positions

### Safety Features

- **Reachability Validation**: Prevents unreachable positions
- **Joint Limit Enforcement**: Hardware and software limits
- **Triangle Inequality**: Mathematical validation
- **Error Recovery**: Fallback to safe positions

### System Integration

- **Thread Safety**: Safe for multi-threaded use
- **Hardware Interface**: Direct servo control
- **Configuration**: YAML-based parameter management
- **Logging**: Comprehensive debug information

---

[← Previous: Robot Movement System](README.md) | [Next: Gait System →](gait_system.md)

[← Back to Documentation](../README.md)