"""
Unit tests for intent dispatcher system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.kws.intent_dispatcher import IntentDispatcher, handler


class TestIntentDispatcher:
    """Test cases for IntentDispatcher class."""
    
    @pytest.fixture
    def mock_task_interface(self):
        """Create a mock task interface."""
        return Mock()
    
    @pytest.fixture
    def dispatcher(self, mock_task_interface):
        """Create an IntentDispatcher instance with mocked task interface."""
        return IntentDispatcher(mock_task_interface)
    
    def test_init(self, mock_task_interface, dispatcher):
        """Test IntentDispatcher initialization."""
        assert dispatcher.task_interface == mock_task_interface
        assert isinstance(dispatcher.intent_handlers, dict)
        assert len(dispatcher.intent_handlers) > 0
        # Check that all expected handlers are registered
        expected_handlers = [
            "help", "system_status", "shut_down", "wake_up", "sleep", "calibrate",
            "repeat", "turn_lights", "change_color", "set_brightness", "set_speed",
            "set_accel", "march_in_place", "idle_stance", "move", "stop", "rotate",
            "follow", "sound_source_localization", "stream_odas_audio", "police",
            "rainbow", "sit_up", "helix", "show_off", "hello", "start_recording",
            "stop_recording"
        ]
        for handler_name in expected_handlers:
            assert handler_name in dispatcher.intent_handlers
    
    def test_dispatch_valid_intent(self, dispatcher, mock_task_interface):
        """Test dispatching a valid intent."""
        slots = {"test": "value"}
        dispatcher.dispatch("help", slots)
        mock_task_interface.hexapod_help.assert_called_once()
    
    def test_dispatch_invalid_intent(self, dispatcher):
        """Test dispatching an invalid intent raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="No handler for intent: invalid_intent"):
            dispatcher.dispatch("invalid_intent", {})
    
    def test_parse_duration_in_seconds_seconds(self, dispatcher):
        """Test parsing duration in seconds."""
        result = dispatcher._parse_duration_in_seconds(30, "seconds")
        assert result == 30.0
    
    def test_parse_duration_in_seconds_minutes(self, dispatcher):
        """Test parsing duration in minutes."""
        result = dispatcher._parse_duration_in_seconds(2, "minutes")
        assert result == 120.0
    
    def test_parse_duration_in_seconds_hours(self, dispatcher):
        """Test parsing duration in hours."""
        result = dispatcher._parse_duration_in_seconds(1, "hours")
        assert result == 3600.0
    
    def test_parse_duration_in_seconds_none_values(self, dispatcher):
        """Test parsing duration with None values."""
        result = dispatcher._parse_duration_in_seconds(None, "seconds")
        assert result is None
        
        result = dispatcher._parse_duration_in_seconds(30, None)
        assert result is None
    
    def test_parse_duration_in_seconds_invalid_value(self, dispatcher):
        """Test parsing duration with invalid value."""
        result = dispatcher._parse_duration_in_seconds("invalid", "seconds")
        assert result is None
    
    def test_parse_duration_in_seconds_invalid_unit(self, dispatcher):
        """Test parsing duration with invalid unit."""
        result = dispatcher._parse_duration_in_seconds(30, "invalid_unit")
        assert result is None
    
    def test_handle_help(self, dispatcher, mock_task_interface):
        """Test handle_help method."""
        slots = {}
        dispatcher.handle_help(slots)
        mock_task_interface.hexapod_help.assert_called_once()
    
    def test_handle_system_status(self, dispatcher, mock_task_interface):
        """Test handle_system_status method."""
        slots = {}
        dispatcher.handle_system_status(slots)
        mock_task_interface.system_status.assert_called_once()
    
    def test_handle_shut_down(self, dispatcher, mock_task_interface):
        """Test handle_shut_down method."""
        slots = {}
        dispatcher.handle_shut_down(slots)
        mock_task_interface.shut_down.assert_called_once()
    
    def test_handle_wake_up(self, dispatcher, mock_task_interface):
        """Test handle_wake_up method."""
        slots = {}
        dispatcher.handle_wake_up(slots)
        mock_task_interface.wake_up.assert_called_once()
    
    def test_handle_sleep(self, dispatcher, mock_task_interface):
        """Test handle_sleep method."""
        slots = {}
        dispatcher.handle_sleep(slots)
        mock_task_interface.sleep.assert_called_once()
    
    def test_handle_calibrate(self, dispatcher, mock_task_interface):
        """Test handle_calibrate method."""
        slots = {}
        dispatcher.handle_calibrate(slots)
        mock_task_interface.calibrate.assert_called_once()
    
    def test_handle_repeat(self, dispatcher, mock_task_interface):
        """Test handle_repeat method."""
        slots = {}
        dispatcher.handle_repeat(slots)
        mock_task_interface.repeat_last_command.assert_called_once()
    
    def test_handle_turn_lights(self, dispatcher, mock_task_interface):
        """Test handle_turn_lights method."""
        slots = {"switch_state": "on"}
        dispatcher.handle_turn_lights(slots)
        mock_task_interface.turn_lights.assert_called_once_with("on")
    
    def test_handle_change_color(self, dispatcher, mock_task_interface):
        """Test handle_change_color method."""
        slots = {"color": "red"}
        dispatcher.handle_change_color(slots)
        mock_task_interface.change_color.assert_called_once_with(color="red")
    
    @patch('hexapod.kws.intent_dispatcher.parse_percentage')
    def test_handle_set_brightness_success(self, mock_parse, dispatcher, mock_task_interface):
        """Test handle_set_brightness method with valid input."""
        mock_parse.return_value = 50
        slots = {"brightness_percentage": "50%"}
        dispatcher.handle_set_brightness(slots)
        mock_parse.assert_called_once_with("50%")
        mock_task_interface.set_brightness.assert_called_once_with(50)
    
    def test_handle_set_brightness_missing_key(self, dispatcher, caplog):
        """Test handle_set_brightness method with missing key."""
        slots = {}
        dispatcher.handle_set_brightness(slots)
        assert "No brightness_percentage provided" in caplog.text
    
    @patch('hexapod.kws.intent_dispatcher.parse_percentage')
    def test_handle_set_brightness_invalid_value(self, mock_parse, dispatcher, caplog):
        """Test handle_set_brightness method with invalid value."""
        mock_parse.side_effect = ValueError("Invalid percentage")
        slots = {"brightness_percentage": "invalid"}
        dispatcher.handle_set_brightness(slots)
        assert "Invalid brightness_percentage value" in caplog.text
    
    @patch('hexapod.kws.intent_dispatcher.parse_percentage')
    def test_handle_set_speed_success(self, mock_parse, dispatcher, mock_task_interface):
        """Test handle_set_speed method with valid input."""
        mock_parse.return_value = 75
        slots = {"speed_percentage": "75%"}
        dispatcher.handle_set_speed(slots)
        mock_parse.assert_called_once_with("75%")
        mock_task_interface.set_speed.assert_called_once_with(75)
    
    def test_handle_set_speed_missing_key(self, dispatcher, caplog):
        """Test handle_set_speed method with missing key."""
        slots = {}
        dispatcher.handle_set_speed(slots)
        assert "No speed_percentage provided" in caplog.text
    
    @patch('hexapod.kws.intent_dispatcher.parse_percentage')
    def test_handle_set_accel_success(self, mock_parse, dispatcher, mock_task_interface):
        """Test handle_set_accel method with valid input."""
        mock_parse.return_value = 25
        slots = {"accel_percentage": "25%"}
        dispatcher.handle_set_accel(slots)
        mock_parse.assert_called_once_with("25%")
        mock_task_interface.set_accel.assert_called_once_with(25)
    
    def test_handle_set_accel_missing_key(self, dispatcher, caplog):
        """Test handle_set_accel method with missing key."""
        slots = {}
        dispatcher.handle_set_accel(slots)
        assert "No accel_percentage provided" in caplog.text
    
    def test_handle_march_in_place_no_duration(self, dispatcher, mock_task_interface):
        """Test handle_march_in_place method without duration."""
        slots = {}
        dispatcher.handle_march_in_place(slots)
        mock_task_interface.march_in_place.assert_called_once_with()
    
    def test_handle_march_in_place_with_duration(self, dispatcher, mock_task_interface):
        """Test handle_march_in_place method with duration."""
        slots = {"march_time": 2, "time_unit": "minutes"}
        dispatcher.handle_march_in_place(slots)
        mock_task_interface.march_in_place.assert_called_once_with(duration=120.0)
    
    def test_handle_march_in_place_invalid_time(self, dispatcher, mock_task_interface, caplog):
        """Test handle_march_in_place method with invalid time."""
        slots = {"march_time": "invalid", "time_unit": "minutes"}
        dispatcher.handle_march_in_place(slots)
        mock_task_interface.march_in_place.assert_called_once_with()
        assert "Invalid march_time value" in caplog.text
    
    def test_handle_idle_stance(self, dispatcher, mock_task_interface):
        """Test handle_idle_stance method."""
        slots = {}
        dispatcher.handle_idle_stance(slots)
        mock_task_interface.idle_stance.assert_called_once()
    
    @patch('hexapod.gait_generator.base_gait.BaseGait')
    def test_handle_move_success(self, mock_base_gait, dispatcher, mock_task_interface):
        """Test handle_move method with valid direction."""
        mock_base_gait.DIRECTION_MAP = {"forward": 0, "backward": 180}
        slots = {"move_direction": "forward"}
        dispatcher.handle_move(slots)
        mock_task_interface.move.assert_called_once_with(direction="forward")
    
    @patch('hexapod.gait_generator.base_gait.BaseGait')
    def test_handle_move_with_cycles(self, mock_base_gait, dispatcher, mock_task_interface):
        """Test handle_move method with cycles."""
        mock_base_gait.DIRECTION_MAP = {"forward": 0, "backward": 180}
        slots = {"move_direction": "forward", "move_cycles": 5}
        dispatcher.handle_move(slots)
        mock_task_interface.move.assert_called_once_with(direction="forward", cycles=5)
    
    @patch('hexapod.gait_generator.base_gait.BaseGait')
    def test_handle_move_with_duration(self, mock_base_gait, dispatcher, mock_task_interface):
        """Test handle_move method with duration."""
        mock_base_gait.DIRECTION_MAP = {"forward": 0, "backward": 180}
        slots = {"move_direction": "forward", "move_time": 30, "time_unit": "seconds"}
        dispatcher.handle_move(slots)
        mock_task_interface.move.assert_called_once_with(direction="forward", duration=30.0)
    
    def test_handle_move_no_direction(self, dispatcher, caplog):
        """Test handle_move method with no direction."""
        slots = {}
        dispatcher.handle_move(slots)
        assert "No direction provided for move command" in caplog.text
    
    @patch('hexapod.gait_generator.base_gait.BaseGait')
    def test_handle_move_invalid_direction(self, mock_base_gait, dispatcher, caplog):
        """Test handle_move method with invalid direction."""
        mock_base_gait.DIRECTION_MAP = {"forward": 0, "backward": 180}
        slots = {"move_direction": "invalid"}
        dispatcher.handle_move(slots)
        assert "Invalid direction 'invalid' for move command" in caplog.text
    
    def test_handle_stop(self, dispatcher, mock_task_interface):
        """Test handle_stop method."""
        slots = {}
        dispatcher.handle_stop(slots)
        mock_task_interface.stop.assert_called_once()
    
    def test_handle_rotate_with_angle(self, dispatcher, mock_task_interface):
        """Test handle_rotate method with angle."""
        slots = {"turn_direction": "left", "rotate_angle": 90}
        dispatcher.handle_rotate(slots)
        mock_task_interface.rotate.assert_called_once_with(turn_direction="left", angle=90.0)
    
    def test_handle_rotate_with_word_angle(self, dispatcher, mock_task_interface):
        """Test handle_rotate method with word angle."""
        slots = {"turn_direction": "right", "rotate_angle": "ninety"}
        dispatcher.handle_rotate(slots)
        mock_task_interface.rotate.assert_called_once_with(turn_direction="right", angle=90.0)
    
    def test_handle_rotate_with_cycles(self, dispatcher, mock_task_interface):
        """Test handle_rotate method with cycles."""
        slots = {"turn_direction": "left", "rotate_cycles": 3}
        dispatcher.handle_rotate(slots)
        mock_task_interface.rotate.assert_called_once_with(turn_direction="left", cycles=3)
    
    def test_handle_rotate_with_duration(self, dispatcher, mock_task_interface):
        """Test handle_rotate method with duration."""
        slots = {"turn_direction": "right", "rotate_time": 10, "time_unit": "seconds"}
        dispatcher.handle_rotate(slots)
        mock_task_interface.rotate.assert_called_once_with(turn_direction="right", duration=10.0)
    
    def test_handle_rotate_invalid_direction(self, dispatcher, caplog):
        """Test handle_rotate method with invalid direction."""
        slots = {"turn_direction": "invalid"}
        dispatcher.handle_rotate(slots)
        assert "Invalid turn_direction 'invalid' for rotate command" in caplog.text
    
    def test_handle_rotate_invalid_angle(self, dispatcher, caplog):
        """Test handle_rotate method with invalid angle."""
        slots = {"turn_direction": "left", "rotate_angle": "invalid"}
        dispatcher.handle_rotate(slots)
        assert "Invalid rotate_angle value" in caplog.text
    
    def test_handle_follow(self, dispatcher, mock_task_interface):
        """Test handle_follow method."""
        slots = {}
        dispatcher.handle_follow(slots)
        mock_task_interface.follow.assert_called_once()
    
    def test_handle_sound_source_localization(self, dispatcher, mock_task_interface):
        """Test handle_sound_source_localization method."""
        slots = {}
        dispatcher.handle_sound_source_localization(slots)
        mock_task_interface.sound_source_localization.assert_called_once()
    
    def test_handle_stream_odas_audio_default(self, dispatcher, mock_task_interface):
        """Test handle_stream_odas_audio method with default stream type."""
        slots = {}
        dispatcher.handle_stream_odas_audio(slots)
        mock_task_interface.stream_odas_audio.assert_called_once_with(stream_type="separated")
    
    def test_handle_stream_odas_audio_custom_type(self, dispatcher, mock_task_interface):
        """Test handle_stream_odas_audio method with custom stream type."""
        slots = {"odas_stream_type": "mixed"}
        dispatcher.handle_stream_odas_audio(slots)
        mock_task_interface.stream_odas_audio.assert_called_once_with(stream_type="mixed")
    
    def test_handle_stream_odas_audio_post_filtered(self, dispatcher, mock_task_interface):
        """Test handle_stream_odas_audio method with post filtered type."""
        slots = {"odas_stream_type": "post filtered"}
        dispatcher.handle_stream_odas_audio(slots)
        mock_task_interface.stream_odas_audio.assert_called_once_with(stream_type="postfiltered")
    
    def test_handle_police(self, dispatcher, mock_task_interface):
        """Test handle_police method."""
        slots = {}
        dispatcher.handle_police(slots)
        mock_task_interface.police.assert_called_once()
    
    def test_handle_rainbow(self, dispatcher, mock_task_interface):
        """Test handle_rainbow method."""
        slots = {}
        dispatcher.handle_rainbow(slots)
        mock_task_interface.rainbow.assert_called_once()
    
    def test_handle_sit_up(self, dispatcher, mock_task_interface):
        """Test handle_sit_up method."""
        slots = {}
        dispatcher.handle_sit_up(slots)
        mock_task_interface.sit_up.assert_called_once()
    
    def test_handle_helix(self, dispatcher, mock_task_interface):
        """Test handle_helix method."""
        slots = {}
        dispatcher.handle_helix(slots)
        mock_task_interface.helix.assert_called_once()
    
    def test_handle_show_off(self, dispatcher, mock_task_interface):
        """Test handle_show_off method."""
        slots = {}
        dispatcher.handle_show_off(slots)
        mock_task_interface.show_off.assert_called_once()
    
    def test_handle_hello(self, dispatcher, mock_task_interface):
        """Test handle_hello method."""
        slots = {}
        dispatcher.handle_hello(slots)
        mock_task_interface.say_hello.assert_called_once()
    
    def test_handle_start_recording_no_duration(self, dispatcher, mock_task_interface):
        """Test handle_start_recording method without duration."""
        slots = {}
        dispatcher.handle_start_recording(slots)
        mock_task_interface.start_recording.assert_called_once_with(duration=None)
    
    def test_handle_start_recording_with_duration(self, dispatcher, mock_task_interface):
        """Test handle_start_recording method with duration."""
        slots = {"record_time": 5, "time_unit": "minutes"}
        dispatcher.handle_start_recording(slots)
        mock_task_interface.start_recording.assert_called_once_with(duration=300.0)
    
    def test_handle_stop_recording(self, dispatcher, mock_task_interface):
        """Test handle_stop_recording method."""
        slots = {}
        dispatcher.handle_stop_recording(slots)
        mock_task_interface.stop_recording.assert_called_once()
    
    def test_handler_decorator(self):
        """Test the handler decorator functionality."""
        mock_logger = Mock()
        with patch('hexapod.kws.intent_dispatcher.logger', mock_logger):
            class TestClass:
                @handler
                def test_method(self, slots):
                    return "test_result"
    
            test_instance = TestClass()
            result = test_instance.test_method({"test": "value"})
    
            # The handler decorator wrapper doesn't return anything (returns None)
            assert result is None
            # Verify logging was called
            mock_logger.info.assert_called_once_with("Handling intent with test_method")
    
    def test_angle_parsing_word_values(self, dispatcher):
        """Test angle parsing with word values."""
        word_angles = {
            "thirty": 30, "sixty": 60, "ninety": 90, "one hundred twenty": 120,
            "two hundred fifty": 250, "one hundred eighty": 180, "two hundred ten": 210,
            "two hundred forty": 240, "two hundred seventy": 270, "three hundred": 300,
            "three hundred thirty": 330, "three hundred sixty": 360
        }
        
        for word, expected_angle in word_angles.items():
            slots = {"turn_direction": "left", "rotate_angle": word}
            dispatcher.handle_rotate(slots)
            # Should work without error
    
    def test_rotate_direction_validation(self, dispatcher):
        """Test rotate direction validation."""
        valid_directions = ["left", "right", "clockwise", "counterclockwise"]
        
        for direction in valid_directions:
            slots = {"turn_direction": direction}
            dispatcher.handle_rotate(slots)
            # Should work without error
    
    @patch('hexapod.gait_generator.base_gait.BaseGait')
    def test_exception_handling_in_handlers(self, mock_base_gait, dispatcher, caplog):
        """Test exception handling in various handlers."""
        # Test march_in_place with exception
        dispatcher.task_interface.march_in_place.side_effect = Exception("Test error")
        slots = {}
        dispatcher.handle_march_in_place(slots)
        assert "Error handling march_in_place intent" in caplog.text
    
        # Test move with exception
        mock_base_gait.DIRECTION_MAP = {"forward": 0, "backward": 180}
        dispatcher.task_interface.move.side_effect = Exception("Test error")
        slots = {"move_direction": "forward"}
        dispatcher.handle_move(slots)
        assert "Error handling move intent" in caplog.text
        
        # Test rotate with exception
        dispatcher.task_interface.rotate.side_effect = Exception("Test error")
        slots = {"turn_direction": "left"}
        dispatcher.handle_rotate(slots)
        assert "Error handling rotate intent" in caplog.text
        
        # Test stream_odas_audio with exception
        dispatcher.task_interface.stream_odas_audio.side_effect = Exception("Test error")
        slots = {}
        dispatcher.handle_stream_odas_audio(slots)
        assert "Error handling stream_odas_audio intent" in caplog.text
        
        # Test start_recording with exception
        dispatcher.task_interface.start_recording.side_effect = Exception("Test error")
        slots = {}
        dispatcher.handle_start_recording(slots)
        assert "Error handling start_recording intent" in caplog.text