# Dual-Mode Gamepad Controller

The hexapod project now features a dual-mode gamepad controller that allows switching between two different control paradigms:

## Overview

The controller supports two distinct modes that can be toggled using the **Options** button:

1. **Body Control Mode** (default): Uses inverse kinematics to move the hexapod's body
2. **Gait Steering Mode**: Uses the gait generator to make the hexapod walk

## Mode Controls

### Toggle Between Modes
- **Options Button**: Press to switch between Body Control and Gait Steering modes
- The current mode is displayed in the console and indicated by LED color

## Body Control Mode

This mode uses inverse kinematics to directly control the hexapod's body position and orientation.

### Controls
- **Left Stick X**: Left/Right translation
- **Left Stick Y**: Forward/Backward translation (inverted)
- **Right Stick X**: Roll rotation (left/right tilt)
- **Right Stick Y**: Pitch rotation (forward/backward tilt)
- **L2/R2 Triggers**: Down/Up translation (analog)
- **L1/R1**: Yaw rotation (left/right turn)

### Characteristics
- Direct control over body position and orientation
- Smooth, continuous movement
- Precise positioning for tasks requiring accuracy
- Movement speed varies with stick deflection
- Deadzone prevents drift from stick center

## Gait Steering Mode

This mode uses the gait generator to create walking movements, making the hexapod actually walk around.

### Controls
- **Left Stick**: Movement direction (forward/backward/left/right)
- **Right Stick X**: Rotation while walking (clockwise/counterclockwise)

### Characteristics
- Natural walking motion using tripod gait
- Direction-independent movement
- Continuous walking with smooth transitions
- Rotation can be combined with forward/backward movement
- Marching in place when no direction is input

## Common Controls

Both modes share these common button controls:

- **Triangle**: Reset to start position
- **Square**: Show current position
- **Circle**: Show help menu
- **PS5**: Exit program

## LED Indicators

The gamepad LED provides visual feedback for the current state:

- **Blue Pulse**: Body control mode (idle)
- **Purple Pulse**: Gait steering mode (idle)
- **Lime Pulse**: Movement detected (both modes)

## Technical Implementation

### Mode Management
- Mode state is tracked in `self.current_mode`
- Mode switching is handled by `_toggle_mode()`
- Input processing is split between `_get_body_control_inputs()` and `_get_gait_steering_inputs()`

### Gait Integration
- Uses `TripodGait` for walking movements
- Gait parameters: step_radius=25.0mm, leg_lift_distance=15.0mm, dwell_time=0.3s
- Gait generation starts/stops automatically with mode switching
- Direction input is normalized and scaled for smooth movement

### Safety Features
- Gait generation is properly stopped when switching modes
- Cleanup ensures gait generation stops on exit
- Movement thresholds prevent unwanted motion
- Proper error handling for mode transitions

## Usage Examples

### Body Control Mode
```python
# Move body forward and up
left_stick_y = -1.0  # Forward
r2_trigger = 1.0     # Up

# Rotate body to the right
right_stick_x = 1.0  # Roll right
r1_button = True     # Yaw right
```

### Gait Steering Mode
```python
# Walk forward
left_stick_y = -1.0  # Forward direction

# Walk forward while turning right
left_stick_y = -1.0  # Forward direction
right_stick_x = 1.0  # Clockwise rotation

# March in place
left_stick_x = 0.0   # No direction
left_stick_y = 0.0   # No direction
```

## Testing

Run the test script to try both modes:

```bash
python test_dual_mode_controller.py
```

This will:
1. Initialize the controller with LED feedback
2. Start in Body Control mode
3. Allow switching between modes using the Options button
4. Provide real-time feedback through console output and LED colors

## Configuration

The controller can be customized by modifying:

- **Sensitivity settings**: `translation_sensitivity`, `rotation_sensitivity`
- **Deadzone**: `deadzone` for analog stick drift prevention
- **Gait parameters**: Step radius, leg lift distance, dwell time
- **LED colors**: Different colors for different states

## Future Enhancements

Potential improvements for the dual-mode controller:

1. **Additional gait types**: Wave gait for more stable movement
2. **Speed control**: Variable walking speed based on stick deflection
3. **Mode memory**: Remember last used mode between sessions
4. **Advanced movements**: Jumping, side-stepping, etc.
5. **Haptic feedback**: Rumble motors for terrain feedback
6. **Voice commands**: Voice control for mode switching 