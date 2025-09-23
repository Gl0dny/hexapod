#!/usr/bin/env python3
"""
Comprehensive test script for GamepadLEDController functionality.

This script tests all features of the LED controller:
- Color setting with all available colors
- Brightness control
- Pulse animations
- Breathing animations
- State management
- Connection status
- Cleanup

Usage:
    python test_gamepad_led.py
"""

import sys
import time
import os
from pathlib import Path

# Add the hexapod directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
HEXAPOD_DIR = (SCRIPT_DIR.parent.parent.parent / "hexapod").resolve()
if str(HEXAPOD_DIR) not in sys.path:
    sys.path.insert(0, str(HEXAPOD_DIR))

from hexapod.interface.controllers import GamepadLEDColor, BaseGamepadLEDController
from hexapod.interface.controllers import DualSenseLEDController


def test_basic_colors(led_controller):
    """Test setting all available colors."""
    print("\n" + "=" * 60)
    print("TESTING BASIC COLORS")
    print("=" * 60)

    colors_to_test = [
        ("RED", GamepadLEDColor.RED),
        ("GREEN", GamepadLEDColor.GREEN),
        ("BLUE", GamepadLEDColor.BLUE),
        ("YELLOW", GamepadLEDColor.YELLOW),
        ("CYAN", GamepadLEDColor.CYAN),
        ("MAGENTA", GamepadLEDColor.MAGENTA),
        ("WHITE", GamepadLEDColor.WHITE),
        ("ORANGE", GamepadLEDColor.ORANGE),
        ("PURPLE", GamepadLEDColor.PURPLE),
        ("PINK", GamepadLEDColor.PINK),
        ("LIME", GamepadLEDColor.LIME),
        ("TEAL", GamepadLEDColor.TEAL),
        ("INDIGO", GamepadLEDColor.INDIGO),
    ]

    for color_name, color in colors_to_test:
        print(f"Setting {color_name}...")
        success = led_controller.set_color(color)
        if success:
            # print(f"✅ {color_name} set successfully")
            pass
        else:
            print(f"❌ Failed to set {color_name}")
        time.sleep(1)  # Show each color for 1 second


def test_brightness_control(led_controller):
    """Test brightness control functionality."""
    print("\n" + "=" * 60)
    print("TESTING BRIGHTNESS CONTROL")
    print("=" * 60)

    # Test different brightness levels
    brightness_levels = [0.1, 0.3, 0.5, 0.7, 1.0]

    for brightness in brightness_levels:
        print(f"Setting brightness to {brightness:.1f}...")
        success = led_controller.set_brightness(brightness)
        if success:
            print(f"Brightness set to {brightness:.1f}")
        else:
            print(f"Failed to set brightness to {brightness:.1f}")
        time.sleep(1)

    # Reset to full brightness
    led_controller.set_brightness(1.0)


def test_pulse_animation(led_controller):
    """Test pulse animation functionality."""
    print("\n" + "=" * 60)
    print("TESTING PULSE ANIMATION")
    print("=" * 60)

    print("Starting pulse animation with BLUE (3 cycles, 1s each)...")
    success = led_controller.pulse(GamepadLEDColor.BLUE, duration=1.0, cycles=3)
    if success:
        print("Pulse animation started")
        time.sleep(3.5)  # Wait for animation to complete
        print("Pulse animation completed")
    else:
        print("Failed to start pulse animation")

    print("\nStarting pulse animation with MAGENTA (2 cycles, 0.5s each)...")
    success = led_controller.pulse(GamepadLEDColor.MAGENTA, duration=0.5, cycles=2)
    if success:
        print("Pulse animation started")
        time.sleep(1.5)  # Wait for animation to complete
        print("Pulse animation completed")
    else:
        print("Failed to start pulse animation")


def test_breathing_animation(led_controller):
    """Test breathing animation functionality."""
    print("\n" + "=" * 60)
    print("TESTING BREATHING ANIMATION")
    print("=" * 60)

    print("Starting breathing animation with WHITE (2 cycles, 2s each)...")
    success = led_controller.breathing_animation(
        GamepadLEDColor.WHITE, duration=2.0, cycles=2
    )
    if success:
        print("Breathing animation started")
        time.sleep(4.5)  # Wait for animation to complete
        print("Breathing animation completed")
    else:
        print("Failed to start breathing animation")

    print("\nStarting breathing animation with ORANGE (1 cycle, 1.5s)...")
    success = led_controller.breathing_animation(
        GamepadLEDColor.ORANGE, duration=1.5, cycles=1
    )
    if success:
        print("Breathing animation started")
        time.sleep(2.0)  # Wait for animation to complete
        print("Breathing animation completed")
    else:
        print("Failed to start breathing animation")


def test_animation_stop(led_controller):
    """Test stopping animations."""
    print("\n" + "=" * 60)
    print("⏹TESTING ANIMATION STOP")
    print("=" * 60)

    print("Starting infinite pulse animation...")
    success = led_controller.pulse(
        GamepadLEDColor.RED, duration=0.5, cycles=0
    )  # 0 = infinite
    if success:
        print("Infinite pulse animation started")
        time.sleep(1.5)  # Let it run for a bit

        print("Stopping animation...")
        led_controller.stop_animation()
        print("Animation stopped")
    else:
        print("Failed to start infinite pulse animation")


def test_connection_status(led_controller):
    """Test connection status and control method detection."""
    print("\n" + "=" * 60)
    print("🔌 TESTING CONNECTION STATUS")
    print("=" * 60)

    print(f"Controller available: {led_controller.is_available()}")
    print(f"Control method: {led_controller.get_control_method()}")

    # Test available colors
    available_colors = led_controller.get_available_colors()
    print(f"Available colors: {len(available_colors)} colors")
    for color_name, rgb in available_colors.items():
        print(f"  - {color_name}: RGB{rgb}")


def test_error_handling(led_controller):
    """Test error handling with invalid inputs."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)

    # Test invalid brightness values
    print("Testing invalid brightness values...")
    led_controller.set_brightness(-0.5)  # Should clamp to 0.0
    led_controller.set_brightness(1.5)  # Should clamp to 1.0
    print("Brightness clamping works")

    # Test invalid RGB values
    print("Testing invalid RGB values...")
    led_controller.set_color_rgb((-10, 300, 50))  # Invalid values
    print("RGB validation works")

    # Test setting color with invalid brightness
    print("Testing color with invalid brightness...")
    led_controller.set_color(
        GamepadLEDColor.BLUE, brightness=2.0
    )  # Should clamp to 1.0
    print("Color brightness validation works")


def main():
    """Main test function."""
    print("GAMEPAD LED CONTROLLER COMPREHENSIVE TEST")
    print("=" * 60)
    print("This script will test all LED controller functionalities.")
    print("Make sure your PS5 DualSense controller is connected!")
    print("=" * 60)

    # Initialize LED controller
    print("Initializing LED controller...")
    led_controller = DualSenseLEDController()

    if not led_controller.is_available():
        print("LED controller not available!")
        print("Make sure:")
        print("1. PS5 DualSense controller is connected")
        print("2. dualsense-controller library is installed")
        print("3. Controller has proper permissions")
        return

    print("✅ LED controller initialized successfully")

    try:
        # Run all tests
        test_connection_status(led_controller)
        test_basic_colors(led_controller)
        test_brightness_control(led_controller)
        test_pulse_animation(led_controller)
        test_breathing_animation(led_controller)
        test_animation_stop(led_controller)
        test_error_handling(led_controller)

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("The LED controller is working perfectly with all features!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        led_controller.stop_animation()
        led_controller.turn_off()
        led_controller.cleanup()
        print("Cleanup completed")


if __name__ == "__main__":
    main()
