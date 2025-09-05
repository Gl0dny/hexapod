# Robot Movement System

[← Previous: Configuration](../core/configuration.md) | [Next: Kinematics →](kinematics.md)

[← Back to Documentation](../README.md)

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [Gait System](#gait-system)
- [Movement Capabilities](#movement-capabilities)
- [Hardware Integration](#hardware-integration)
- [Control Interface](#control-interface)
- [Performance Characteristics](#performance-characteristics)

---

## Overview

The Robot Movement System is the core locomotion engine for the hexapod robot. It manages all aspects of movement from basic servo control to complex gait patterns, inverse kinematics calculations, and balance compensation. The system provides a comprehensive framework for controlling 18 servo motors across 6 legs to achieve smooth, stable, and intelligent movement.

## System Architecture

### Movement System Components

```mermaid
graph TB
    subgraph "Robot Movement System"
        subgraph "Core Control"
            H[Hexapod<br/>• Main Controller<br/>• 18 Servo Management<br/>• Position Tracking]
            GG[Gait Generator<br/>• Pattern Execution<br/>• State Management<br/>• Thread Coordination]
        end
        
        subgraph "Leg Control"
            L[Leg Class<br/>• Individual Leg Control<br/>• Inverse Kinematics<br/>• Joint Management]
            J[Joint Class<br/>• Servo Control<br/>• Angle Validation<br/>• Safety Limits]
        end
        
        subgraph "Movement Patterns"
            TG[Tripod Gait<br/>• 3+3 Leg Groups<br/>• High Stability<br/>• Efficient Movement]
            WG[Wave Gait<br/>• Sequential Movement<br/>• Maximum Stability<br/>• Precise Control]
        end
        
        subgraph "Hardware Integration"
            MU[Maestro UART<br/>• Servo Communication<br/>• Real-time Control<br/>• Safety Management]
            BC[Balance Compensator<br/>• IMU Integration<br/>• Stability Control<br/>• Fall Prevention]
        end
    end
    
    H --> GG
    H --> L
    L --> J
    GG --> TG
    GG --> WG
    H --> MU
    H --> BC
    J --> MU
```

### Movement Execution Flow

```mermaid
flowchart LR
    MC[Movement Command] --> GG[Gait Generation]
    GG --> IK[Inverse Kinematics]
    IK --> LP[Leg Positioning]
    LP --> SC[Servo Control]
    SC --> PF[Position Feedback]
    PF --> STC[Stability Check]
    STC --> MC2[Movement Complete]
```

## Core Components

### 1. **Hexapod Class** (`src/robot/hexapod.py`)

**Role**: Main robot controller and movement coordinator
- Manages all 18 servos across 6 legs
- Coordinates movement commands and execution
- Handles position tracking and state management
- Provides high-level movement interface

**Key Features**:
- **Servo Management**: Direct control of 18 MG996R servos via Pololu Maestro
- **Position Tracking**: Real-time tracking of leg positions and angles
- **Movement Commands**: High-level movement interface (move_body, move_to_position)
- **Safety Systems**: Emergency stop, position validation, angle limits
- **Configuration**: YAML-based configuration for geometry and parameters

### 2. **Leg Class** (`src/robot/leg.py`)

**Role**: Individual leg control and kinematics
- Manages 3 servos per leg (coxa, femur, tibia)
- Calculates inverse kinematics for foot positioning
- Handles joint angle validation and limits
- Provides leg-specific movement control

**Key Features**:
- **Inverse Kinematics**: Geometric calculations for foot positioning
- **Joint Management**: Individual servo control and validation
- **Angle Validation**: Hardware and software joint limits
- **Position Control**: Precise foot positioning in 3D space

### 3. **Joint Class** (`src/robot/joint.py`)

**Role**: Individual servo control and management
- Controls servo position, speed, and acceleration
- Handles servo communication and safety limits
- Provides angle validation and error handling
- Manages servo-specific parameters

**Key Features**:
- **Servo Control**: Direct servo communication via Maestro UART
- **Angle Validation**: Hardware and software limits
- **Safety Management**: Emergency stop and position limits
- **Parameter Control**: Speed and acceleration management

### 4. **Gait Generator** (`src/gait_generator/gait_generator.py`)

**Role**: Gait pattern execution and coordination
- Manages gait state machine and execution
- Coordinates leg movements and timing
- Handles continuous movement in separate thread
- Provides gait switching and parameter control

**Key Features**:
- **Thread-based Execution**: Continuous movement without blocking
- **State Management**: Gait phase coordination and transitions
- **Timing Control**: Precise timing for smooth movement
- **Gait Switching**: Dynamic switching between gait patterns

## Gait System

### **Tripod Gait** (`src/gait_generator/tripod_gait.py`)

**Pattern**: 3+3 leg groups alternating movement
- **Group A**: Legs 0, 2, 4 (Right, Left Front, Left Back)
- **Group B**: Legs 1, 3, 5 (Right Front, Left, Right Back)
- **Stability**: 3 legs always supporting the robot
- **Efficiency**: Fastest and most stable gait pattern

**Key Features**:
- **Circle-based Targeting**: Direction-independent movement
- **Simultaneous Movement**: Swing and stance legs move together
- **Stability**: Maintains support polygon throughout movement
- **Efficiency**: Optimal balance of speed and stability

### **Wave Gait** (`src/gait_generator/wave_gait.py`)

**Pattern**: Sequential leg movement (one at a time)
- **Sequence**: 0 → 1 → 2 → 3 → 4 → 5 → 0 → ...
- **Stability**: 5 legs always supporting the robot
- **Precision**: Maximum stability for precise movements

**Key Features**:
- **Sequential Movement**: One leg moves at a time
- **Maximum Stability**: 5 legs always supporting
- **Precise Control**: Ideal for delicate operations
- **Slow but Stable**: Trade speed for maximum stability

### **Base Gait System** (`src/gait_generator/base_gait.py`)

**Role**: Abstract base class for all gait patterns
- **Circle-based Targeting**: Direction-independent movement
- **Three-phase Path Planning**: Lift → Travel → Lower for swing legs
- **Vector Mathematics**: Clean mathematical operations
- **Extensible Design**: Easy to add new gait patterns

**Key Features**:
- **Direction Independence**: Same gait works for any movement direction
- **Path Planning**: Smooth trajectories with waypoints
- **Mathematical Foundation**: Vector-based calculations
- **Extensibility**: Easy to implement new gait patterns

## Movement Capabilities

### **Basic Movements**

- **Standing**: Stable standing position with all legs supporting
- **Walking**: Forward, backward, left, right with various gaits
- **Turning**: Smooth turning with different radius options
- **Positioning**: Move to specific coordinates or orientations

### **Advanced Movements**

- **Body Movement**: Translation and rotation of the robot body
- **Leg Positioning**: Individual leg control and positioning
- **Predefined Positions**: Zero, high profile, low profile positions
- **Gait Switching**: Dynamic switching between gait patterns

### **Movement Commands**

- **`move_body(tx, ty, tz, roll, pitch, yaw)`**: Body translation and rotation
- **`move_to_position(position)`**: Move to predefined positions
- **`move_all_legs(positions)`**: Move all legs to specific positions
- **`move_leg_angles(leg, coxa, femur, tibia)`**: Direct leg angle control

## Hardware Integration

### **Servo Control**

- **18 MG996R Servos**: High-torque servos with precise positioning
- **Pololu Maestro Controller**: 24-channel servo controller via UART
- **Real-time Control**: 50Hz update rate for smooth movement
- **Safety Management**: Emergency stop and position limits

### **Sensor Integration**

- **ICM-20948 IMU**: 9-axis inertial measurement unit
- **Balance Compensation**: IMU-based stability control
- **Position Feedback**: Real-time position and angle tracking
- **Safety Monitoring**: Continuous stability assessment

### **Communication**

- **UART Communication**: Serial communication with servo controller
- **Thread Safety**: Thread-safe servo control and updates
- **Error Handling**: Robust error handling and recovery
- **Status Monitoring**: Real-time status and error reporting

## Control Interface

### **High-Level Interface**

- **Movement Commands**: Simple, intuitive movement commands
- **Position Control**: Precise positioning and orientation
- **Gait Selection**: Easy switching between gait patterns
- **Safety Controls**: Emergency stop and safety features

### **Configuration Interface**

- **YAML Configuration**: Easy parameter adjustment
- **Geometry Settings**: Robot geometry and dimensions
- **Servo Parameters**: Speed, acceleration, and limits
- **Gait Parameters**: Step radius, timing, and behavior

### **Status Interface**

- **Position Tracking**: Real-time position and angle information
- **Status Monitoring**: Movement status and error reporting
- **Performance Metrics**: Timing and performance data
- **Debug Information**: Detailed debugging and logging

## Performance Characteristics

### **Movement Performance**

- **Servo Update Rate**: 50Hz for smooth movement
- **Position Accuracy**: ±2mm for foot positioning
- **Gait Transition**: < 100ms between different gait patterns
- **Response Time**: < 50ms from command to execution

### **Safety Features**

- **Emergency Stop**: Immediate servo deactivation
- **Position Limits**: Hardware and software joint limits
- **Stability Monitoring**: Continuous balance assessment
- **Safe Shutdown**: Graceful movement to safe positions

### **System Reliability**

- **Error Handling**: Robust error handling and recovery
- **Thread Safety**: Thread-safe operation and updates
- **Resource Management**: Efficient resource usage and cleanup
- **Status Monitoring**: Continuous system health monitoring

---

[← Previous: Configuration](../core/configuration.md) | [Next: Kinematics →](kinematics.md)

[← Back to Documentation](../README.md)