# IMU Data Format and Interpretation

[← Previous: Hardware Integration](hardware_integration.md) | [Next: Lights System →](lights_system.md)

[← Back to Documentation](../README.md)

## Table of Contents

- [Overview](#overview)
- [Hardware Specifications](#hardware-specifications)
- [Data Format](#data-format)
- [Sensor Data Interpretation](#sensor-data-interpretation)

---

## Overview

The IMU (Inertial Measurement Unit) system provides real-time sensor data for orientation tracking in the hexapod robot. The system uses the ICM-20948 9-DOF sensor to provide acceleration, gyroscope, magnetometer, and temperature data.

## Hardware Specifications

### **ICM-20948 Sensor**

**Sensor Type**: 9-DOF Inertial Measurement Unit
- **Accelerometer**: 3-axis acceleration measurement
- **Gyroscope**: 3-axis angular velocity measurement  
- **Magnetometer**: 3-axis magnetic field measurement
- **Temperature**: Built-in temperature sensor

**Communication**: I2C interface
**Integration**: Direct integration with Raspberry Pi via I2C bus

## Data Format

### **Accelerometer Data** (`get_acceleration()`)

**Units**: Gravity (g) - where 1.0 g = 9.81 m/s²
**Format**: `(ax, ay, az)` - Tuple of three float values
**Range**: Typically -2g to +2g per axis

**Example Output**:
```
Accel: X=00.01 Y=00.01 Z=01.01
```

**Interpretation**:
- **X-axis**: Forward/backward acceleration
- **Y-axis**: Left/right acceleration  
- **Z-axis**: Vertical acceleration (gravity when stationary)

### **Gyroscope Data** (`get_gyroscope()`)

**Units**: Degrees per second (°/s)
**Format**: `(gx, gy, gz)` - Tuple of three float values
**Range**: Typically -2000°/s to +2000°/s per axis

**Example Output**:
```
Gyro: X=00.46 Y=01.14 Z=-0.35
```

**Interpretation**:
- **X-axis**: Pitch rate (forward/backward rotation)
- **Y-axis**: Roll rate (left/right rotation)
- **Z-axis**: Yaw rate (clockwise/counterclockwise rotation)

### **Magnetometer Data** (`get_magnetometer()`)

**Units**: Microteslas (µT)
**Format**: `(mx, my, mz)` - Tuple of three float values
**Range**: Typically -4900 µT to +4900 µT per axis

**Example Output**:
```
Mag: X=-4.95 Y=-6.30 Z=103.95
```

**Interpretation**:
- **X-axis**: Magnetic field strength along X-axis
- **Y-axis**: Magnetic field strength along Y-axis
- **Z-axis**: Magnetic field strength along Z-axis (typically strongest)

### **Temperature Data** (`get_temperature()`)

**Units**: Degrees Celsius (°C)
**Format**: Single float value
**Range**: Typically -40°C to +85°C

**Example Output**:
```
Temp: 33.11
```

**Interpretation**:
- **Temperature**: Sensor operating temperature
- **Typical Range**: 20°C to 40°C for normal operation

## Sensor Data Interpretation

### **Accelerometer Interpretation**

**Stationary Robot (Flat Surface)**:
- **X ≈ 0.0**: No forward/backward tilt
- **Y ≈ 0.0**: No left/right tilt
- **Z ≈ 1.0**: Gravity pointing downward

**Forward Tilt**:
- **X becomes negative**: Forward acceleration
- **Y remains near 0**: No lateral tilt
- **Z decreases slightly**: Reduced vertical component

**Backward Tilt**:
- **X becomes positive**: Backward acceleration
- **Y remains near 0**: No lateral tilt
- **Z decreases slightly**: Reduced vertical component

**Left Tilt**:
- **X remains near 0**: No forward/backward tilt
- **Y becomes negative**: Left acceleration
- **Z decreases slightly**: Reduced vertical component

**Right Tilt**:
- **X remains near 0**: No forward/backward tilt
- **Y becomes positive**: Right acceleration
- **Z decreases slightly**: Reduced vertical component

### **Gyroscope Interpretation**

**Stationary Robot**:
- **All values near 0.0**: No rotation detected

**During Movement**:
- **Positive X**: Rotating forward/down (pitch down)
- **Negative X**: Rotating backward/up (pitch up)
- **Positive Y**: Rotating right (roll right)
- **Negative Y**: Rotating left (roll left)
- **Positive Z**: Rotating clockwise (yaw right)
- **Negative Z**: Rotating counterclockwise (yaw left)

### **Magnetometer Interpretation**

**Magnetic Field Strength**:
- **X-axis**: Horizontal magnetic field component
- **Y-axis**: Horizontal magnetic field component
- **Z-axis**: Vertical magnetic field component (typically strongest)

**Orientation Reference**:
- **Z-axis dominance**: Indicates sensor orientation relative to Earth's magnetic field
- **X/Y variations**: Indicate rotation around vertical axis


---

[← Previous: Hardware Integration](hardware_integration.md) | [Next: Lights System →](lights_system.md)

[← Back to Documentation](../README.md)
