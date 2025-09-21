"""
Unit tests for lights system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.lights.lights import Lights, ColorRGB


@pytest.fixture
def mock_apa102():
    """Mock APA102 driver."""
    mock_driver = Mock()
    mock_driver.num_led = 12
    mock_driver.global_brightness = 15
    mock_driver.set_pixel = Mock()
    mock_driver.show = Mock()
    mock_driver.rotate = Mock()
    return mock_driver


@pytest.fixture
def mock_led():
    """Mock LED power control."""
    mock_led = Mock()
    mock_led.on = Mock()
    mock_led.off = Mock()
    return mock_led


@pytest.fixture
def lights_default(mock_apa102, mock_led):
    """Lights instance with default parameters."""
    with (
        patch("hexapod.lights.lights.APA102", return_value=mock_apa102),
        patch("hexapod.lights.lights.LED", return_value=mock_led),
        patch("hexapod.lights.lights.logger"),
    ):
        return Lights()


@pytest.fixture
def lights_custom(mock_apa102, mock_led):
    """Lights instance with custom parameters."""
    with (
        patch("hexapod.lights.lights.APA102", return_value=mock_apa102),
        patch("hexapod.lights.lights.LED", return_value=mock_led),
        patch("hexapod.lights.lights.logger"),
    ):
        return Lights(
            num_led=8, power_pin=18, brightness=75, initial_color=ColorRGB.RED
        )


class TestColorRGB:
    """Test cases for ColorRGB enum."""

    def test_color_values(self):
        """Test that all colors have correct RGB values."""
        assert ColorRGB.BLACK.rgb == (0, 0, 0)
        assert ColorRGB.BLUE.rgb == (0, 0, 255)
        assert ColorRGB.TEAL.rgb == (0, 128, 128)
        assert ColorRGB.GREEN.rgb == (0, 255, 0)
        assert ColorRGB.LIME.rgb == (75, 180, 0)
        assert ColorRGB.YELLOW.rgb == (255, 215, 0)
        assert ColorRGB.GOLDEN.rgb == (255, 50, 0)
        assert ColorRGB.ORANGE.rgb == (255, 25, 0)
        assert ColorRGB.RED.rgb == (255, 0, 0)
        assert ColorRGB.PINK.rgb == (255, 51, 183)
        assert ColorRGB.PURPLE.rgb == (128, 0, 128)
        assert ColorRGB.INDIGO.rgb == (75, 0, 130)
        assert ColorRGB.GRAY.rgb == (139, 69, 19)
        assert ColorRGB.WHITE.rgb == (255, 255, 255)

    def test_rgb_property(self):
        """Test that rgb property returns the value."""
        assert ColorRGB.RED.rgb == ColorRGB.RED.value
        assert isinstance(ColorRGB.RED.rgb, tuple)
        assert len(ColorRGB.RED.rgb) == 3

    def test_all_colors_valid_rgb(self):
        """Test that all colors have valid RGB values."""
        for color in ColorRGB:
            rgb = color.rgb
            assert isinstance(rgb, tuple)
            assert len(rgb) == 3
            assert all(isinstance(val, int) and 0 <= val <= 255 for val in rgb)


class TestLights:
    """Test cases for Lights class."""

    def test_init_default_parameters(self, mock_apa102, mock_led):
        """Test Lights initialization with default parameters."""
        with (
            patch(
                "hexapod.lights.lights.APA102", return_value=mock_apa102
            ) as mock_apa102_class,
            patch("hexapod.lights.lights.LED", return_value=mock_led) as mock_led_class,
            patch("hexapod.lights.lights.logger") as mock_logger,
        ):

            lights = Lights()

            assert lights.num_led == 12
            assert lights.driver == mock_apa102
            assert lights.power == mock_led
            assert lights.led_color == ColorRGB.INDIGO
            assert lights.brightness == 50

            # Verify initialization calls
            mock_apa102_class.assert_called_once_with(num_led=12)
            mock_led_class.assert_called_once_with(5)
            mock_led.on.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Lights initialized successfully with 12 LEDs."
            )

    def test_init_custom_parameters(self, mock_apa102, mock_led):
        """Test Lights initialization with custom parameters."""
        with (
            patch(
                "hexapod.lights.lights.APA102", return_value=mock_apa102
            ) as mock_apa102_class,
            patch("hexapod.lights.lights.LED", return_value=mock_led) as mock_led_class,
            patch("hexapod.lights.lights.logger") as mock_logger,
        ):

            lights = Lights(
                num_led=8, power_pin=18, brightness=75, initial_color=ColorRGB.RED
            )

            assert lights.num_led == 8
            assert lights.driver == mock_apa102
            assert lights.power == mock_led
            assert lights.led_color == ColorRGB.RED
            assert lights.brightness == 75

            # Verify initialization calls
            mock_apa102_class.assert_called_once_with(num_led=8)
            mock_led_class.assert_called_once_with(18)
            mock_led.on.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Lights initialized successfully with 8 LEDs."
            )

    def test_constants(self):
        """Test class constants."""
        assert Lights.DEFAULT_NUM_LED == 12
        assert Lights.DEFAULT_POWER_PIN == 5

    def test_set_brightness_valid(self, lights_default):
        """Test setting valid brightness levels."""
        # Test normal brightness
        lights_default.set_brightness(50)
        assert lights_default.brightness == 50
        assert lights_default.driver.global_brightness == int(0b11111 * 50 / 100)

        # Test maximum brightness
        lights_default.set_brightness(100)
        assert lights_default.brightness == 100
        assert lights_default.driver.global_brightness == int(0b11111 * 100 / 100)

        # Test minimum brightness
        lights_default.set_brightness(0)
        assert lights_default.brightness == 0
        assert lights_default.driver.global_brightness == int(0b11111 * 0 / 100)

    def test_set_brightness_clamping(self, lights_default):
        """Test brightness clamping for out-of-range values."""
        # Test above maximum
        lights_default.set_brightness(150)
        assert lights_default.brightness == 100

        # Test below minimum
        lights_default.set_brightness(-50)
        assert lights_default.brightness == 0

    def test_set_color_valid_enum(self, lights_default):
        """Test setting color with valid ColorRGB enum."""
        lights_default.set_color(ColorRGB.RED)

        # Verify driver calls
        assert lights_default.driver.set_pixel.call_count == 12  # All LEDs
        lights_default.driver.set_pixel.assert_any_call(0, 255, 0, 0)  # RED
        lights_default.driver.show.assert_called_once()

    def test_set_color_specific_led(self, lights_default):
        """Test setting color for specific LED."""
        lights_default.set_color(ColorRGB.BLUE, led_index=5)

        # Verify only one LED was set
        lights_default.driver.set_pixel.assert_called_once_with(5, 0, 0, 255)  # BLUE
        lights_default.driver.show.assert_called_once()

    def test_set_color_specific_count(self, lights_default):
        """Test setting color for specific number of LEDs."""
        lights_default.set_color(ColorRGB.GREEN, num_led=3)

        # Verify only 3 LEDs were set
        assert lights_default.driver.set_pixel.call_count == 3
        lights_default.driver.set_pixel.assert_any_call(0, 0, 255, 0)  # GREEN
        lights_default.driver.set_pixel.assert_any_call(1, 0, 255, 0)
        lights_default.driver.set_pixel.assert_any_call(2, 0, 255, 0)
        lights_default.driver.show.assert_called_once()

    def test_set_color_invalid_type(self, lights_default):
        """Test setting color with invalid type."""
        with pytest.raises(ValueError, match="Invalid color: invalid_color"):
            lights_default.set_color("invalid_color")

    def test_set_color_led_index_out_of_range(self, lights_default):
        """Test setting color with LED index out of range."""
        with pytest.raises(ValueError, match="LED index 15 is out of range"):
            lights_default.set_color(ColorRGB.RED, led_index=15)

    def test_set_color_rgb_valid(self, lights_default):
        """Test setting color with valid RGB tuple."""
        lights_default.set_color_rgb((128, 64, 192))

        # Verify driver calls
        assert lights_default.driver.set_pixel.call_count == 12  # All LEDs
        lights_default.driver.set_pixel.assert_any_call(0, 128, 64, 192)
        lights_default.driver.show.assert_called_once()

    def test_set_color_rgb_specific_led(self, lights_default):
        """Test setting RGB color for specific LED."""
        lights_default.set_color_rgb((255, 128, 0), led_index=3)

        # Verify only one LED was set
        lights_default.driver.set_pixel.assert_called_once_with(3, 255, 128, 0)
        lights_default.driver.show.assert_called_once()

    def test_set_color_rgb_specific_count(self, lights_default):
        """Test setting RGB color for specific number of LEDs."""
        lights_default.set_color_rgb((0, 255, 128), num_led=5)

        # Verify only 5 LEDs were set
        assert lights_default.driver.set_pixel.call_count == 5
        lights_default.driver.set_pixel.assert_any_call(0, 0, 255, 128)
        lights_default.driver.show.assert_called_once()

    def test_set_color_rgb_invalid_tuple(self, lights_default):
        """Test setting color with invalid RGB tuple."""
        # Test wrong type
        with pytest.raises(ValueError, match="Invalid RGB tuple"):
            lights_default.set_color_rgb("invalid")

        # Test wrong length
        with pytest.raises(ValueError, match="Invalid RGB tuple"):
            lights_default.set_color_rgb((128, 64))

        # Test invalid values
        with pytest.raises(ValueError, match="Invalid RGB tuple"):
            lights_default.set_color_rgb((256, 64, 128))

        with pytest.raises(ValueError, match="Invalid RGB tuple"):
            lights_default.set_color_rgb((128, -1, 64))

    def test_set_color_rgb_led_index_out_of_range(self, lights_default):
        """Test setting RGB color with LED index out of range."""
        with pytest.raises(ValueError, match="LED index 20 is out of range"):
            lights_default.set_color_rgb((128, 64, 192), led_index=20)

    def test_rotate(self, lights_default):
        """Test LED rotation."""
        lights_default.rotate(3)

        lights_default.driver.rotate.assert_called_once_with(3)
        lights_default.driver.show.assert_called_once()

    def test_rotate_negative(self, lights_default):
        """Test LED rotation with negative value."""
        lights_default.rotate(-2)

        lights_default.driver.rotate.assert_called_once_with(-2)
        lights_default.driver.show.assert_called_once()

    def test_rotate_default(self, lights_default):
        """Test LED rotation with default value."""
        lights_default.rotate()

        lights_default.driver.rotate.assert_called_once_with(1)
        lights_default.driver.show.assert_called_once()

    def test_get_wheel_color_green_to_red(self, lights_default):
        """Test color wheel in green to red transition."""
        # Test at position 0 (pure green)
        color = lights_default.get_wheel_color(0)
        assert color == (0, 255, 0)

        # Test at position 42 (middle of green to red)
        color = lights_default.get_wheel_color(42)
        assert color == (126, 129, 0)

        # Test at position 84 (almost red)
        color = lights_default.get_wheel_color(84)
        assert color == (252, 3, 0)

    def test_get_wheel_color_red_to_blue(self, lights_default):
        """Test color wheel in red to blue transition."""
        # Test at position 85 (pure red)
        color = lights_default.get_wheel_color(85)
        assert color == (255, 0, 0)

        # Test at position 127 (middle of red to blue)
        color = lights_default.get_wheel_color(127)
        assert color == (129, 0, 126)

        # Test at position 169 (almost blue)
        color = lights_default.get_wheel_color(169)
        assert color == (3, 0, 252)

    def test_get_wheel_color_blue_to_green(self, lights_default):
        """Test color wheel in blue to green transition."""
        # Test at position 170 (pure blue)
        color = lights_default.get_wheel_color(170)
        assert color == (0, 0, 255)

        # Test at position 212 (middle of blue to green)
        color = lights_default.get_wheel_color(212)
        assert color == (0, 126, 129)

        # Test at position 255 (almost green)
        color = lights_default.get_wheel_color(255)
        assert color == (0, 255, 0)

    def test_get_wheel_color_wrap_around(self, lights_default):
        """Test color wheel wrap-around behavior."""
        # Test position > 255 wraps around
        color1 = lights_default.get_wheel_color(300)
        color2 = lights_default.get_wheel_color(44)  # 300 % 256 = 44
        assert color1 == color2

        # Test position < 0 wraps around
        color1 = lights_default.get_wheel_color(-10)
        color2 = lights_default.get_wheel_color(246)  # -10 % 256 = 246
        assert color1 == color2

    def test_clear_all_leds(self, lights_default):
        """Test clearing all LEDs."""
        lights_default.clear()

        # Verify all LEDs are cleared
        assert lights_default.driver.set_pixel.call_count == 12
        for i in range(12):
            lights_default.driver.set_pixel.assert_any_call(i, 0, 0, 0)
        lights_default.driver.show.assert_called_once()

    def test_clear_specific_leds(self, lights_default):
        """Test clearing specific LEDs."""
        lights_default.clear(led_indices=[0, 2, 4, 6])

        # Verify only specified LEDs are cleared
        assert lights_default.driver.set_pixel.call_count == 4
        lights_default.driver.set_pixel.assert_any_call(0, 0, 0, 0)
        lights_default.driver.set_pixel.assert_any_call(2, 0, 0, 0)
        lights_default.driver.set_pixel.assert_any_call(4, 0, 0, 0)
        lights_default.driver.set_pixel.assert_any_call(6, 0, 0, 0)
        lights_default.driver.show.assert_called_once()

    def test_clear_count(self, lights_default):
        """Test clearing specific number of LEDs from start."""
        lights_default.clear(count=5)

        # Verify only first 5 LEDs are cleared
        assert lights_default.driver.set_pixel.call_count == 5
        for i in range(5):
            lights_default.driver.set_pixel.assert_any_call(i, 0, 0, 0)
        lights_default.driver.show.assert_called_once()

    def test_clear_priority(self, lights_default):
        """Test that led_indices takes priority over count."""
        lights_default.clear(led_indices=[1, 3], count=5)

        # Should use led_indices, not count
        assert lights_default.driver.set_pixel.call_count == 2
        lights_default.driver.set_pixel.assert_any_call(1, 0, 0, 0)
        lights_default.driver.set_pixel.assert_any_call(3, 0, 0, 0)
        lights_default.driver.show.assert_called_once()

    def test_brightness_calculation(self, lights_default):
        """Test brightness calculation formula."""
        # Test 50% brightness
        lights_default.set_brightness(50)
        expected = int(0b11111 * 50 / 100)  # 0b11111 = 31
        assert lights_default.driver.global_brightness == expected

        # Test 25% brightness
        lights_default.set_brightness(25)
        expected = int(0b11111 * 25 / 100)
        assert lights_default.driver.global_brightness == expected

        # Test 100% brightness
        lights_default.set_brightness(100)
        expected = int(0b11111 * 100 / 100)
        assert lights_default.driver.global_brightness == expected

    def test_initial_color_setting(self, mock_apa102, mock_led):
        """Test that initial color is stored during initialization."""
        with (
            patch("hexapod.lights.lights.APA102", return_value=mock_apa102),
            patch("hexapod.lights.lights.LED", return_value=mock_led),
            patch("hexapod.lights.lights.logger"),
        ):

            lights = Lights(initial_color=ColorRGB.BLUE)

            # Verify initial color was stored
            assert lights.led_color == ColorRGB.BLUE
            # The set_brightness call should have been made
            assert lights.brightness == 50  # Default brightness
            # But no color setting should have occurred during init
            assert mock_apa102.set_pixel.call_count == 0

    def test_driver_integration(self, lights_default):
        """Test integration with APA102 driver."""
        # Test that all methods properly call driver methods
        lights_default.set_color(ColorRGB.RED)
        lights_default.driver.set_pixel.assert_called()
        lights_default.driver.show.assert_called()

        # Reset mocks
        lights_default.driver.set_pixel.reset_mock()
        lights_default.driver.show.reset_mock()

        lights_default.rotate(2)
        lights_default.driver.rotate.assert_called_once_with(2)
        lights_default.driver.show.assert_called_once()

    def test_error_handling_invalid_color_enum(self, lights_default):
        """Test error handling for invalid color enum values."""

        # Create a mock color that's not a ColorRGB instance
        class FakeColor:
            def __init__(self):
                self.rgb = (255, 0, 0)

        fake_color = FakeColor()

        with pytest.raises(ValueError, match="Invalid color"):
            lights_default.set_color(fake_color)

    def test_error_handling_invalid_rgb_from_enum(self, lights_default):
        """Test error handling for ColorRGB with invalid RGB values."""

        # This is a theoretical test since ColorRGB values are hardcoded
        # But it tests the validation logic
        class BadColorRGB:
            def __init__(self):
                self.rgb = (256, -1, 300)  # Invalid RGB values

        bad_color = BadColorRGB()

        # Mock isinstance to return True for our bad color
        with patch("hexapod.lights.lights.isinstance", return_value=True):
            with pytest.raises(ValueError, match="Invalid RGB tuple"):
                lights_default.set_color(bad_color)
