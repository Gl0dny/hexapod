import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def lights_module():
    """Import the real lights module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "lights_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/lights.py"
    )
    lights_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lights_module)
    return lights_module


class TestLights:
    """Test the Lights class from lights.py"""

    def test_lights_initialization(self, lights_module, mock_apa102, mock_led):
        """Test Lights class initialization."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            
            # Verify initialization
            assert lights.brightness == 50
            assert lights.driver.global_brightness == int(0b11111 * 50 / 100)
            mock_apa102.assert_called_with(num_led=12)
            mock_led.assert_called_with(5)
            mock_led.return_value.on.assert_called_once()

    def test_set_brightness(self, lights_module, mock_apa102, mock_led):
        """Test brightness setting."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            
            # Test normal brightness
            lights.set_brightness(75)
            assert lights.brightness == 75
            assert lights.driver.global_brightness == int(0b11111 * 75 / 100)
            
            # Test max brightness
            lights.set_brightness(120)
            assert lights.brightness == 100
            assert lights.driver.global_brightness == 31
            
            # Test min brightness
            lights.set_brightness(-10)
            assert lights.brightness == 0
            assert lights.driver.global_brightness == 0

    def test_set_color_rgb(self, lights_module, mock_apa102, mock_led):
        """Test RGB color setting."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            lights.set_color_rgb((10, 20, 30))
            
            # Verify all LEDs were set
            for i in range(12):
                lights.driver.set_pixel.assert_any_call(i, 10, 20, 30)
            lights.driver.show.assert_called_once()

    def test_set_color_enum(self, lights_module, mock_apa102, mock_led):
        """Test color enum setting."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            lights.set_color(lights_module.ColorRGB.RED)
            
            # Verify all LEDs were set to red
            for i in range(12):
                lights.driver.set_pixel.assert_any_call(i, 255, 0, 0)
            lights.driver.show.assert_called_once()

    def test_set_color_invalid(self, lights_module, mock_apa102, mock_led):
        """Test invalid color handling."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            
            # Test invalid color type
            with pytest.raises(ValueError):
                lights.set_color("INVALID")
            
            with pytest.raises(ValueError):
                lights.set_color(123)

    def test_set_color_rgb_invalid(self, lights_module, mock_apa102, mock_led):
        """Test invalid RGB color handling."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            
            # Test wrong number of values
            with pytest.raises(ValueError):
                lights.set_color_rgb((255, 255))
            
            # Test invalid value types
            with pytest.raises(ValueError):
                lights.set_color_rgb((255, '255', 255))
            
            # Test negative values
            with pytest.raises(ValueError):
                lights.set_color_rgb((-1, 255, 255))
            
            # Test wrong container type
            with pytest.raises(ValueError):
                lights.set_color_rgb([255, 255, 255])

    def test_rotate(self, lights_module, mock_apa102, mock_led):
        """Test LED rotation."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            lights.rotate(3)
            
            lights.driver.rotate.assert_called_with(3)
            lights.driver.show.assert_called()

    def test_get_wheel_color(self, lights_module, mock_apa102, mock_led):
        """Test wheel color calculation."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            
            # Test wheel color calculation
            assert lights.get_wheel_color(0) == (0, 255, 0)    # Green
            assert lights.get_wheel_color(85) == (255, 0, 0)   # Red
            assert lights.get_wheel_color(170) == (0, 0, 255)  # Blue

    def test_clear(self, lights_module, mock_apa102, mock_led):
        """Test LED clearing."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            lights.clear(led_indices=[1, 2])
            
            # Verify specific LEDs were cleared
            lights.driver.set_pixel.assert_any_call(1, 0, 0, 0)
            lights.driver.set_pixel.assert_any_call(2, 0, 0, 0)
            lights.driver.show.assert_called()

    def test_clear_all(self, lights_module, mock_apa102, mock_led):
        """Test clearing all LEDs."""
        with patch.object(lights_module, 'APA102', mock_apa102), \
             patch.object(lights_module, 'LED', mock_led):
            
            lights = lights_module.Lights()
            lights.clear()
            
            # Verify all LEDs were cleared
            for i in range(12):
                lights.driver.set_pixel.assert_any_call(i, 0, 0, 0)
            lights.driver.show.assert_called()

    def test_color_rgb_enum_values(self, lights_module):
        """Test ColorRGB enum values."""
        assert lights_module.ColorRGB.RED.value == (255, 0, 0)
        assert lights_module.ColorRGB.GREEN.value == (0, 255, 0)
        assert lights_module.ColorRGB.BLUE.value == (0, 0, 255)
        assert lights_module.ColorRGB.WHITE.value == (255, 255, 255)
        assert lights_module.ColorRGB.BLACK.value == (0, 0, 0)
        assert lights_module.ColorRGB.YELLOW.value == (255, 215, 0)
        assert lights_module.ColorRGB.TEAL.value == (0, 128, 128)
        assert lights_module.ColorRGB.PURPLE.value == (128, 0, 128)
