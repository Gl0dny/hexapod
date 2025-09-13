# Dual-Mode Gamepad Controller

[← Previous: Voice Control Interface](voice_control_interface.md) | [Next: Voice Control System →](../voice/voice_control_system.md)

[← Back to Documentation](../README.md)

## Table of Contents

- [Overview](#overview)
- [Controller Architecture](#controller-architecture)
- [Control Modes](#control-modes)
- [Input Mapping](#input-mapping)
- [LED Feedback System](#led-feedback-system)
- [Configuration](#configuration)
- [Usage](#usage)

---

## Overview

The hexapod project features a sophisticated dual-mode gamepad controller that provides intuitive manual control of the hexapod robot. The controller supports two distinct control paradigms that can be toggled during operation, offering both precise body positioning and natural walking movement.

**Key Features**:
- **Dual Control Modes**: Body control (inverse kinematics) and gait control (walking movement)
- **PS5 DualSense Support**: Full support for PlayStation 5 DualSense controller via USB and Bluetooth
- **LED Feedback**: Visual feedback through controller LED lightbar
- **Sensitivity Control**: Adjustable sensitivity for all movement types
- **Voice Control Integration**: Seamless switching between manual and voice control
- **Real-time Status**: Comprehensive status reporting and position feedback

## Controller Architecture

### **GamepadHexapodController** (`src/interface/controllers/gamepad_hexapod_controller.py`)

**Role**: Main gamepad controller implementation
- **Base Class**: Extends `ManualHexapodController` (threading.Thread)
- **Input Processing**: Handles gamepad input via pygame library
- **Mode Management**: Manages switching between control modes
- **LED Control**: Provides visual feedback through controller LEDs

**Key Components**:
- **Input Mapping**: `DualSenseUSBMapping` for button/axis mapping
- **LED Controller**: `DualSenseLEDController` for visual feedback
- **Gait Integration**: Direct integration with hexapod gait generator
- **Sensitivity Management**: Real-time sensitivity adjustment

### **Base Manual Controller** (`src/interface/controllers/base_manual_controller.py`)

**Role**: Abstract base class for all manual controllers
- **Threading**: Runs as daemon thread with configurable update rate (20 Hz)
- **Movement Processing**: Handles both body control and gait control logic
- **State Management**: Tracks current position and movement state
- **Mode Switching**: Provides framework for mode transitions

**Movement Parameters**:
- **Translation Step**: 6.0 mm per analog unit
- **Rotation Steps**: 2.0° (roll/pitch), 4.0° (yaw) per input
- **Z Movement**: 4.0 mm per analog unit
- **Gait Stance Height**: 2.0 mm per L2/R2 press

## Control Modes

### **Body Control Mode** (Default)

**Purpose**: Direct control of hexapod body position and orientation using inverse kinematics

**Controls**:
- **Left Stick X**: Left/Right translation (tx)
- **Left Stick Y**: Forward/Backward translation (ty) - inverted
- **Right Stick X**: Roll rotation (left/right tilt)
- **Right Stick Y**: Pitch rotation (forward/backward tilt)
- **L2/R2 Triggers**: Down/Up translation (tz) - analog
- **L1/R1**: Yaw rotation (left/right turn)

**Characteristics**:
- **Direct Control**: Immediate response to stick input
- **Precise Positioning**: Ideal for tasks requiring accuracy
- **Smooth Movement**: Continuous, proportional control
- **Deadzone**: Prevents drift from stick center position

### **Gait Control Mode**

**Purpose**: Natural walking movement using the hexapod's gait generator

**Controls**:
- **Left Stick**: Movement direction (forward/backward/left/right/diagonal)
- **Right Stick X**: Rotation while walking (clockwise/counterclockwise)
- **X Button**: Toggle marching in place (neutral gait)

**Characteristics**:
- **Natural Walking**: Uses tripod gait for realistic movement
- **Direction Independence**: Smooth transitions between directions
- **Combined Movement**: Translation and rotation can be combined
- **Marching Mode**: Continuous walking when enabled

## Input Mapping

### **DualSense USB Mapping** (`src/interface/input_mappings/dual_sense_usb_mapping.py`)

**Axis Mappings**:
- **Left Stick**: X=0, Y=1 (inverted)
- **Right Stick**: X=2, Y=3 (inverted)
- **Triggers**: L2=4, R2=5 (analog)

**Button Mappings**:
- **Face Buttons**: X=0, Circle=1, Square=2, Triangle=3
- **Shoulder Buttons**: L1=9, R1=10
- **System Buttons**: Options=6, PS5=5, Create=4
- **Stick Buttons**: L3=7, R3=8
- **D-pad**: Up=11, Down=12, Left=13, Right=14 (as buttons)

**Special Features**:
- **D-pad as Buttons**: USB mode uses buttons instead of hat for D-pad
- **Analog Triggers**: L2/R2 provide continuous analog input
- **Interface Detection**: Auto-detects "dualsense", "ps5", "playstation 5"

### **Input Processing**

**Deadzone Handling**:
- **Default Deadzone**: 0.1 (10% stick movement required)
- **Sensitivity Scaling**: 0.1 to 1.0 range with 0.1 step increments
- **Button Debouncing**: 0.3 second cooldown between button presses

**Analog Input Processing**:
- **Raw Values**: -1.0 to +1.0 from pygame
- **Sensitivity Application**: Multiplied by current sensitivity setting
- **Step Scaling**: Applied based on movement type and mode

## LED Feedback System

### **DualSense LED Controller** (`src/interface/controllers/gamepad_led_controllers/dual_sense_led_controller.py`)

**Role**: Provides visual feedback through PS5 DualSense lightbar
- **Color Management**: RGB color control with smooth transitions
- **Mode Indication**: Different colors for different control modes
- **Status Feedback**: Visual confirmation of controller state

**LED Colors by Mode**:
- **Body Control**: Blue pulsing animation
- **Gait Control**: Indigo thinking animation
- **Voice Control**: Inherits from voice control system
- **Error States**: Red indication for errors

**Technical Implementation**:
- **Library**: `dualsense-controller` Python package
- **Connection**: USB or Bluetooth (auto-detection)
- **Microphone**: Initially muted to avoid audio conflicts
- **Error Handling**: Graceful fallback if LED control unavailable

## Configuration

### **Sensitivity Settings**

**Translation Sensitivity**:
- **Body Mode**: Controls translation step scaling
- **Gait Mode**: Controls direction input scaling
- **Range**: 0.1 to 1.0 (10% to 100%)
- **Default**: 0.5 (50%)

**Rotation Sensitivity**:
- **Body Mode**: Controls rotation step scaling
- **Gait Mode**: Controls rotation input scaling
- **Range**: 0.1 to 1.0 (10% to 100%)
- **Default**: 0.5 (50%)

**Adjustment Controls**:
- **D-pad Left/Right**: Translation sensitivity (±0.1)
- **D-pad Up/Down**: Rotation sensitivity (±0.1)
- **Real-time**: Changes apply immediately

### **Gait Parameters**

**Translation Gait**:
- **Step Radius**: Configurable step size
- **Leg Lift Distance**: Height of leg lift during swing
- **Stance Height**: Base height of stance legs
- **Dwell Time**: Time spent in each gait phase

**Rotation Gait**:
- **Separate Instance**: Independent gait for pure rotation
- **Optimized Parameters**: Tuned for rotation movement
- **Automatic Switching**: Based on input type

## Usage

### **Starting the Controller**

**Command Line**:
```bash
python src/interface/controllers/gamepad_hexapod_controller.py
```

**Integration**:
- **Main Application**: Automatically initialized if gamepad available
- **Dependency Check**: Graceful fallback if pygame unavailable
- **Threading**: Runs as daemon thread alongside main application

### **Mode Switching**

**Options Button**:
- **Toggle**: Switch between Body Control and Gait Control
- **Visual Feedback**: LED color changes to indicate mode
- **Console Output**: Mode change confirmation with control instructions
- **State Reset**: Position reset when switching modes

**Voice Control Toggle**:
- **PS5 Button**: Switch between manual and voice control
- **Pause/Resume**: Manual control pauses when voice active
- **Mode Memory**: Returns to previous manual mode when resuming

### **Common Controls**

**Universal Buttons**:
- **Triangle**: Reset to start position
- **Square**: Show current position/status
- **Circle**: Print help information
- **PS5**: Toggle voice control mode (if available)

**Status Display**:
- **Body Mode**: Shows current translation and rotation values
- **Gait Mode**: Shows gait status, direction, and leg positions
- **Sensitivity**: Always displays current sensitivity levels

### **Advanced Features**

**Marching Mode** (Gait Control):
- **X Button**: Toggle continuous neutral gait
- **Purpose**: Allows continuous walking without direction input
- **Status**: Console indication when enabled/disabled

**Stance Height Control**:
- **L2/R2**: Adjust gait stance height in gait mode
- **Range**: -40.0 to +40.0 mm
- **Real-time**: Changes apply immediately to active gait

**Sensitivity Adjustment**:
- **D-pad**: Fine-tune sensitivity during operation
- **Persistence**: Settings maintained during session
- **Mode-specific**: Separate settings for body and gait modes

---

[← Previous: Voice Control Interface](voice_control_interface.md) | [Next: Voice Control System →](../voice/voice_control_system.md)

[← Back to Documentation](../README.md)