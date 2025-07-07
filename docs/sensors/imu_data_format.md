# IMU Data Format and Interpretation

This document describes the format and interpretation of IMU (Inertial Measurement Unit) data from the hexapod robot.

## Data Format

The IMU provides two types of measurements:
1. Accelerometer (Accel) - measures acceleration in m/s²
2. Gyroscope (Gyro) - measures angular velocity in degrees per second

The data is presented in the format:
```
Accel: X=±X.XX Y=±Y.XX Z=±Z.XX | Gyro: X=±X.XX Y=±Y.XX Z=±Z.XX
```

## Accelerometer Interpretation

The accelerometer measures acceleration along three axes:
- X: Forward/backward tilt
- Y: Left/right tilt
- Z: Vertical acceleration (gravity)

### Expected Values

1. Flat Surface:
   - X ≈ 0.0
   - Y ≈ 0.0
   - Z ≈ 1.0 (gravity)

2. Forward Tilt:
   - X becomes negative
   - Y remains near 0
   - Z decreases slightly

3. Backward Tilt:
   - X becomes positive
   - Y remains near 0
   - Z decreases slightly

4. Left Tilt:
   - X remains near 0
   - Y becomes negative
   - Z decreases slightly

5. Right Tilt:
   - X remains near 0
   - Y becomes positive
   - Z decreases slightly

## Gyroscope Interpretation

The gyroscope measures rotation speed around three axes:
- X: Pitch rate (forward/backward rotation)
- Y: Roll rate (left/right rotation)
- Z: Yaw rate (clockwise/counterclockwise rotation)

### Expected Values

1. Stationary:
   - All values near 0.0

2. During Movement:
   - Positive X: Rotating forward/down
   - Negative X: Rotating backward/up
   - Positive Y: Rotating right
   - Negative Y: Rotating left
   - Positive Z: Rotating clockwise
   - Negative Z: Rotating counterclockwise

## Example Readings

### Flat Surface
```
Accel: X=+0.01 Y=-0.01 Z=+1.02 | Gyro: X=+0.54 Y=+0.60 Z=-0.11
```

### Forward Tilt
```
Accel: X=-0.40 Y=-0.10 Z=+0.93 | Gyro: X=+0.81 Y=+3.40 Z=-0.09
```

### Backward Tilt
```
Accel: X=+0.28 Y=+0.03 Z=+0.98 | Gyro: X=+3.15 Y=-1.60 Z=-2.38
```

### Left Tilt
```
Accel: X=-0.12 Y=-0.54 Z=+0.86 | Gyro: X=+3.69 Y=-0.88 Z=-1.11
```

### Right Tilt
```
Accel: X=-0.05 Y=+0.35 Z=+0.94 | Gyro: X=+0.70 Y=+0.95 Z=-2.98
```

## Usage in Balance Compensation

The IMU data is used by the `BalanceCompensator` class to:
1. Detect tilts using accelerometer data
2. Measure rotation rates using gyroscope data
3. Apply appropriate compensation to maintain balance

### Compensation Strategy
The compensator uses a proportional approach:
- All tilts are compensated, regardless of size
- Compensation is scaled based on the tilt angle
- Small tilts result in small, gentle movements
- Larger tilts result in proportionally larger movements

### Key Parameters
- Compensation factor: 0.1 (base scaling factor for all movements)
- Maximum compensation angle: 5.0 degrees (safety limit)
- Minimum movement threshold: 0.5 degrees (prevents tiny jitters)

The compensation is calculated as:
```
compensation_angle = tilt_angle * compensation_factor
```

This ensures smooth, proportional responses to all tilts while preventing excessive movements.

## Testing

Use the `test_imu.py` script to test and verify IMU readings:
```bash
python tests/test_robot/test_sensors/test_imu.py
```

The script provides:
1. Initial orientation test
2. Systematic tilt testing
3. Gyroscope-specific testing 