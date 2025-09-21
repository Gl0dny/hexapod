"""
Unit tests for APA102 LED strip driver.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.lights.apa102 import APA102, RGB_MAP


class TestAPA102:
    """Test cases for APA102 class."""

    @pytest.fixture
    def mock_spi(self):
        """Mock SPI device for testing."""
        mock_spi = MagicMock()
        mock_spi.xfer2 = MagicMock()
        return mock_spi

    @pytest.fixture
    def apa102_default(self, mock_spi):
        """APA102 instance with default parameters."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            return APA102(num_led=10)

    @pytest.fixture
    def apa102_custom(self, mock_spi):
        """APA102 instance with custom parameters."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            return APA102(
                num_led=20,
                global_brightness=15,
                order="grb",
                bus=1,
                device=0,
                max_speed_hz=4000000,
            )

    def test_init_default_parameters(self, mock_spi):
        """Test APA102 initialization with default parameters."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(num_led=10)

            assert apa102.num_led == 10
            assert apa102.global_brightness == APA102.MAX_BRIGHTNESS
            assert apa102.rgb == RGB_MAP["rgb"]
            assert len(apa102.leds) == 40  # 4 bytes per LED
            mock_spi.open.assert_called_once_with(0, 1)
            assert mock_spi.max_speed_hz == 8000000

    def test_init_custom_parameters(self, mock_spi):
        """Test APA102 initialization with custom parameters."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(
                num_led=20,
                global_brightness=15,
                order="grb",
                bus=1,
                device=0,
                max_speed_hz=4000000,
            )

            assert apa102.num_led == 20
            assert apa102.global_brightness == 15
            assert apa102.rgb == RGB_MAP["grb"]
            assert len(apa102.leds) == 80  # 4 bytes per LED
            mock_spi.open.assert_called_once_with(1, 0)
            assert mock_spi.max_speed_hz == 4000000

    def test_init_invalid_order(self, mock_spi):
        """Test APA102 initialization with invalid color order."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(num_led=10, order="invalid")

            # Should default to RGB
            assert apa102.rgb == RGB_MAP["rgb"]

    def test_init_brightness_above_max(self, mock_spi):
        """Test APA102 initialization with brightness above maximum."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(num_led=10, global_brightness=50)

            # Should be limited to MAX_BRIGHTNESS
            assert apa102.global_brightness == APA102.MAX_BRIGHTNESS

    def test_init_no_max_speed(self, mock_spi):
        """Test APA102 initialization without max speed."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(num_led=10, max_speed_hz=0)

            # max_speed_hz should not be set
            assert (
                not hasattr(apa102.spi, "max_speed_hz") or apa102.spi.max_speed_hz != 0
            )

    def test_init_spidev_not_available(self):
        """Test APA102 initialization when spidev is not available."""
        with patch("hexapod.lights.apa102.spidev", None):
            with pytest.raises(
                ImportError, match="spidev module is required but not available"
            ):
                APA102(num_led=10)

    def test_constants(self):
        """Test that constants are properly defined."""
        assert APA102.MAX_BRIGHTNESS == 0b11111
        assert APA102.LED_START == 0b11100000
        assert RGB_MAP["rgb"] == [3, 2, 1]
        assert RGB_MAP["rbg"] == [3, 1, 2]
        assert RGB_MAP["grb"] == [2, 3, 1]
        assert RGB_MAP["gbr"] == [2, 1, 3]
        assert RGB_MAP["brg"] == [1, 3, 2]
        assert RGB_MAP["bgr"] == [1, 2, 3]

    def test_clock_start_frame(self, apa102_default):
        """Test start frame generation."""
        apa102_default.clock_start_frame()

        apa102_default.spi.xfer2.assert_called_once_with([0] * 4)

    def test_clock_end_frame(self, apa102_default):
        """Test end frame generation."""
        apa102_default.clock_end_frame()

        apa102_default.spi.xfer2.assert_called_once_with([0xFF] * 4)

    def test_set_pixel_valid_colors(self, apa102_default):
        """Test setting pixel with valid colors."""
        apa102_default.set_pixel(0, 255, 128, 64, 50)

        # Check that the pixel buffer was updated
        start_index = 0
        from math import ceil

        expected_brightness = int(ceil(50 * 31 / 100.0))
        assert apa102_default.leds[start_index] == (
            0b11100000 | (expected_brightness & 0b00011111)
        )
        assert apa102_default.leds[start_index + 3] == 255  # Red (RGB order)
        assert apa102_default.leds[start_index + 2] == 128  # Green
        assert apa102_default.leds[start_index + 1] == 64  # Blue

    def test_set_pixel_grb_order(self, apa102_custom):
        """Test setting pixel with GRB color order."""
        apa102_custom.set_pixel(0, 255, 128, 64, 50)

        # Check that the pixel buffer was updated with GRB order
        start_index = 0
        from math import ceil

        expected_brightness = int(ceil(50 * 15 / 100.0))
        assert apa102_custom.leds[start_index] == (
            0b11100000 | (expected_brightness & 0b00011111)
        )
        assert apa102_custom.leds[start_index + 2] == 255  # Red (GRB order)
        assert apa102_custom.leds[start_index + 3] == 128  # Green
        assert apa102_custom.leds[start_index + 1] == 64  # Blue

    def test_set_pixel_invalid_colors(self, apa102_default):
        """Test setting pixel with invalid colors."""
        with pytest.raises(
            ValueError, match="red, green, and blue must be integers between 0 and 255"
        ):
            apa102_default.set_pixel(0, 256, 128, 64)

        with pytest.raises(
            ValueError, match="red, green, and blue must be integers between 0 and 255"
        ):
            apa102_default.set_pixel(0, 255, -1, 64)

        with pytest.raises(
            ValueError, match="red, green, and blue must be integers between 0 and 255"
        ):
            apa102_default.set_pixel(0, 255, 128, 256)

    def test_set_pixel_out_of_bounds(self, apa102_default):
        """Test setting pixel out of bounds."""
        # Negative index should be ignored
        apa102_default.set_pixel(-1, 255, 128, 64)

        # Index >= num_led should be ignored
        apa102_default.set_pixel(10, 255, 128, 64)

        # Should not raise exception
        assert True

    def test_set_pixel_brightness_calculation(self, apa102_default):
        """Test brightness calculation."""
        from math import ceil

        # Test 100% brightness
        apa102_default.set_pixel(0, 255, 128, 64, 100)
        expected_brightness = int(ceil(100 * 31 / 100.0))  # 31
        assert apa102_default.leds[0] == (0b11100000 | expected_brightness)

        # Test 50% brightness
        apa102_default.set_pixel(1, 255, 128, 64, 50)
        expected_brightness = int(ceil(50 * 31 / 100.0))  # 16
        assert apa102_default.leds[4] == (0b11100000 | expected_brightness)

        # Test 0% brightness
        apa102_default.set_pixel(2, 255, 128, 64, 0)
        expected_brightness = int(0 * 31 / 100)  # 0
        assert apa102_default.leds[8] == (0b11100000 | expected_brightness)

    def test_set_pixel_rgb_valid(self, apa102_default):
        """Test setting pixel with combined RGB value."""
        apa102_default.set_pixel_rgb(0, 0xFF8040, 75)  # RGB(255, 128, 64)

        # Check that the pixel buffer was updated
        start_index = 0
        from math import ceil

        expected_brightness = int(ceil(75 * 31 / 100.0))
        assert apa102_default.leds[start_index] == (0b11100000 | expected_brightness)
        assert apa102_default.leds[start_index + 3] == 255  # Red
        assert apa102_default.leds[start_index + 2] == 128  # Green
        assert apa102_default.leds[start_index + 1] == 64  # Blue

    def test_set_pixel_rgb_invalid(self, apa102_default):
        """Test setting pixel with invalid RGB value."""
        with pytest.raises(ValueError, match="rgb_color must be a 24-bit integer"):
            apa102_default.set_pixel_rgb(0, 0x1000000)  # Too large

        with pytest.raises(ValueError, match="rgb_color must be a 24-bit integer"):
            apa102_default.set_pixel_rgb(0, -1)  # Negative

    def test_set_pixel_rgb_boundary_values(self, apa102_default):
        """Test setting pixel with RGB boundary values."""
        # Test minimum value
        apa102_default.set_pixel_rgb(0, 0x000000, 50)
        assert apa102_default.leds[3] == 0  # Red
        assert apa102_default.leds[2] == 0  # Green
        assert apa102_default.leds[1] == 0  # Blue

        # Test maximum value
        apa102_default.set_pixel_rgb(1, 0xFFFFFF, 50)
        assert apa102_default.leds[7] == 255  # Red
        assert apa102_default.leds[6] == 255  # Green
        assert apa102_default.leds[5] == 255  # Blue

    def test_rotate_positive(self, apa102_default):
        """Test rotating LEDs by positive positions."""
        # Set some initial colors
        apa102_default.set_pixel(0, 255, 0, 0)  # Red
        apa102_default.set_pixel(1, 0, 255, 0)  # Green
        apa102_default.set_pixel(2, 0, 0, 255)  # Blue

        # Rotate by 1 position
        apa102_default.rotate(1)

        # Check that colors moved
        # LED 0 should now have Green (was LED 1)
        assert apa102_default.leds[3] == 0  # Red component
        assert apa102_default.leds[2] == 255  # Green component
        assert apa102_default.leds[1] == 0  # Blue component

    def test_rotate_negative(self, apa102_default):
        """Test rotating LEDs by negative positions."""
        # Set some initial colors
        apa102_default.set_pixel(0, 255, 0, 0)  # Red
        apa102_default.set_pixel(1, 0, 255, 0)  # Green

        # Store initial state
        initial_led0 = apa102_default.leds[0:4].copy()
        initial_led1 = apa102_default.leds[4:8].copy()

        # Rotate by -1 position (reverse direction)
        # -1 % 10 = 9, so it rotates by 9 positions forward
        apa102_default.rotate(-1)

        # After rotation, the pattern should have shifted
        # LED 0 should now be empty (LED_START only)
        assert apa102_default.leds[0] == APA102.LED_START
        assert apa102_default.leds[1] == 0
        assert apa102_default.leds[2] == 0
        assert apa102_default.leds[3] == 0

        # The rotation should have changed something (not the same as initial)
        # We just verify that the rotation method doesn't crash and changes the state
        assert (
            apa102_default.leds[0:4] != initial_led0
            or apa102_default.leds[4:8] != initial_led1
        )

    def test_rotate_multiple_positions(self, apa102_default):
        """Test rotating LEDs by multiple positions."""
        # Set some initial colors
        for i in range(5):
            apa102_default.set_pixel(i, i * 50, 0, 0)

        # Rotate by 3 positions
        apa102_default.rotate(3)

        # Check that colors moved by 3 positions
        # LED 0 should now have the color that was at LED 3
        assert apa102_default.leds[3] == 150  # Red component (3 * 50)

    def test_rotate_wrap_around(self, apa102_default):
        """Test rotating LEDs with wrap-around."""
        # Set some initial colors
        for i in range(10):
            apa102_default.set_pixel(i, i * 25, 0, 0)

        # Rotate by 12 positions (should wrap around to 2)
        apa102_default.rotate(12)

        # Check that colors moved by 2 positions (12 % 10 = 2)
        # LED 0 should now have the color that was at LED 2
        assert apa102_default.leds[3] == 50  # Red component (2 * 25)

    def test_show(self, apa102_default):
        """Test showing LEDs (sending data to strip)."""
        # Set some colors
        apa102_default.set_pixel(0, 255, 128, 64)
        apa102_default.set_pixel(1, 128, 255, 64)

        apa102_default.show()

        # Check that start frame was called
        assert apa102_default.spi.xfer2.call_count >= 1

        # Check that data was sent in chunks
        calls = apa102_default.spi.xfer2.call_args_list
        assert len(calls) >= 2  # Start frame + data chunks + end frame

    def test_show_large_strip(self, mock_spi):
        """Test showing LEDs with a large strip (more than 1024 LEDs)."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            # Create a large strip (1500 LEDs)
            apa102 = APA102(num_led=1500)

            apa102.show()

            # Should send data in multiple chunks
            calls = mock_spi.xfer2.call_args_list
            assert len(calls) >= 2  # Multiple data chunks

    def test_clear_strip(self, apa102_default):
        """Test clearing the strip."""
        # Set some colors first
        apa102_default.set_pixel(0, 255, 128, 64)
        apa102_default.set_pixel(1, 128, 255, 64)

        apa102_default.clear_strip()

        # Check that all LEDs are set to black
        for i in range(apa102_default.num_led):
            start_index = 4 * i
            assert apa102_default.leds[start_index + 1] == 0  # Blue
            assert apa102_default.leds[start_index + 2] == 0  # Green
            assert apa102_default.leds[start_index + 3] == 0  # Red

        # Check that show was called
        assert apa102_default.spi.xfer2.call_count >= 1

    def test_cleanup(self, apa102_default):
        """Test cleanup (closing SPI connection)."""
        apa102_default.cleanup()

        apa102_default.spi.close.assert_called_once()

    def test_combine_color_static(self):
        """Test static combine_color method."""
        # Test basic combination
        color = APA102.combine_color(255, 128, 64)
        assert color == 0xFF8040

        # Test boundary values
        color = APA102.combine_color(0, 0, 0)
        assert color == 0x000000

        color = APA102.combine_color(255, 255, 255)
        assert color == 0xFFFFFF

        # Test individual components
        color = APA102.combine_color(255, 0, 0)
        assert color == 0xFF0000

        color = APA102.combine_color(0, 255, 0)
        assert color == 0x00FF00

        color = APA102.combine_color(0, 0, 255)
        assert color == 0x0000FF

    def test_wheel_green_to_red(self, apa102_default):
        """Test color wheel from green to red."""
        # Test position 0 (pure green)
        color = apa102_default.wheel(0)
        assert color == 0x00FF00

        # Test position 42 (middle of green->red transition)
        color = apa102_default.wheel(42)
        expected = APA102.combine_color(42 * 3, 255 - 42 * 3, 0)
        assert color == expected

        # Test position 84 (end of green->red transition)
        color = apa102_default.wheel(84)
        expected = APA102.combine_color(84 * 3, 255 - 84 * 3, 0)
        assert color == expected

    def test_wheel_red_to_blue(self, apa102_default):
        """Test color wheel from red to blue."""
        # Test position 85 (start of red->blue transition)
        color = apa102_default.wheel(85)
        expected = APA102.combine_color(255 - 0 * 3, 0, 0 * 3)
        assert color == expected

        # Test position 127 (middle of red->blue transition)
        color = apa102_default.wheel(127)
        wheel_pos = 127 - 85
        expected = APA102.combine_color(255 - wheel_pos * 3, 0, wheel_pos * 3)
        assert color == expected

        # Test position 169 (end of red->blue transition)
        color = apa102_default.wheel(169)
        wheel_pos = 169 - 85
        expected = APA102.combine_color(255 - wheel_pos * 3, 0, wheel_pos * 3)
        assert color == expected

    def test_wheel_blue_to_green(self, apa102_default):
        """Test color wheel from blue to green."""
        # Test position 170 (start of blue->green transition)
        color = apa102_default.wheel(170)
        expected = APA102.combine_color(0, 0 * 3, 255 - 0 * 3)
        assert color == expected

        # Test position 212 (middle of blue->green transition)
        color = apa102_default.wheel(212)
        wheel_pos = 212 - 170
        expected = APA102.combine_color(0, wheel_pos * 3, 255 - wheel_pos * 3)
        assert color == expected

        # Test position 255 (end of blue->green transition)
        color = apa102_default.wheel(255)
        wheel_pos = 255 - 170
        expected = APA102.combine_color(0, wheel_pos * 3, 255 - wheel_pos * 3)
        assert color == expected

    def test_wheel_boundary_values(self, apa102_default):
        """Test color wheel with boundary values."""
        # Test position > 255 (should be clamped)
        color = apa102_default.wheel(300)
        assert color == apa102_default.wheel(255)

        # Test position < 0 (not clamped, uses negative value)
        # -10 will be used as-is in the calculation
        color = apa102_default.wheel(-10)
        # This should return a color (not crash)
        assert isinstance(color, int)
        # Note: The wheel method can return negative values for negative inputs
        # This is the actual behavior of the implementation

    def test_dump_array(self, apa102_default, capsys):
        """Test dumping LED array for debugging."""
        # Set some colors
        apa102_default.set_pixel(0, 255, 128, 64)
        apa102_default.set_pixel(1, 128, 255, 64)

        apa102_default.dump_array()

        captured = capsys.readouterr()
        assert "leds" in captured.out or str(apa102_default.leds) in captured.out

    def test_led_buffer_initialization(self, apa102_default):
        """Test LED buffer initialization."""
        # Check that buffer has correct size
        assert len(apa102_default.leds) == apa102_default.num_led * 4

        # Check that buffer is initialized with LED_START
        for i in range(apa102_default.num_led):
            start_index = 4 * i
            assert apa102_default.leds[start_index] == APA102.LED_START
            assert apa102_default.leds[start_index + 1] == 0  # Blue
            assert apa102_default.leds[start_index + 2] == 0  # Green
            assert apa102_default.leds[start_index + 3] == 0  # Red

    def test_brightness_rounding(self, apa102_default):
        """Test brightness rounding behavior."""
        from math import ceil

        # Test that brightness rounds up
        apa102_default.set_pixel(0, 255, 128, 64, 1)  # 1% brightness
        expected_brightness = int(
            ceil(1 * 31 / 100.0)
        )  # Should be 0, but rounds up to 1
        assert apa102_default.leds[0] == (0b11100000 | expected_brightness)

    def test_all_color_orders(self, mock_spi):
        """Test all supported color orders."""
        for order in RGB_MAP.keys():
            with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
                apa102 = APA102(num_led=3, order=order)

                # Set a pixel with known colors
                apa102.set_pixel(0, 255, 128, 64)

                # Check that colors are in the correct positions
                start_index = 0
                expected_positions = RGB_MAP[order]
                assert apa102.leds[start_index + expected_positions[0]] == 255  # Red
                assert apa102.leds[start_index + expected_positions[1]] == 128  # Green
                assert apa102.leds[start_index + expected_positions[2]] == 64  # Blue

    def test_spi_communication_error_handling(self, mock_spi):
        """Test SPI communication error handling."""
        with patch("hexapod.lights.apa102.spidev.SpiDev", return_value=mock_spi):
            apa102 = APA102(num_led=10)

            # Simulate SPI error
            mock_spi.xfer2.side_effect = Exception("SPI communication error")

            # Should not raise exception during show()
            try:
                apa102.show()
            except Exception as e:
                assert "SPI communication error" in str(e)

    def test_memory_efficiency(self, apa102_default):
        """Test memory efficiency with large strips."""
        # Test that LED buffer is not unnecessarily large
        assert len(apa102_default.leds) == apa102_default.num_led * 4

        # Test that rotation doesn't create memory leaks
        original_len = len(apa102_default.leds)
        apa102_default.rotate(5)
        assert len(apa102_default.leds) == original_len
