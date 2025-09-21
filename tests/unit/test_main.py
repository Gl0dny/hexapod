"""
Unit tests for main application entry point.
"""
import pytest
import sys
import threading
import time
import argparse
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from hexapod.main import (
    main, shutdown_callback, handle_button_interactions, shutdown_cleanup,
    create_main_parser, create_application_components, initialize_manual_controller,
    run_main_loop, shutdown_event
)
from hexapod.robot import PredefinedPosition


class TestShutdownCallback:
    """Test cases for shutdown_callback function."""
    
    def setup_method(self):
        """Setup method to ensure clean state before each test."""
        from hexapod.main import shutdown_event
        shutdown_event.clear()
    
    def teardown_method(self):
        """Teardown method to ensure clean state after each test."""
        from hexapod.main import shutdown_event
        shutdown_event.clear()
    
    def test_shutdown_callback_sets_event(self):
        """Test that shutdown_callback sets the shutdown event."""
        # Reset the event before test
        shutdown_event.clear()
        assert not shutdown_event.is_set()
        
        shutdown_callback()
        
        assert shutdown_event.is_set()
    
    def test_shutdown_callback_multiple_calls(self):
        """Test that multiple calls to shutdown_callback work correctly."""
        shutdown_event.clear()
        
        shutdown_callback()
        assert shutdown_event.is_set()
        
        # Second call should still work
        shutdown_callback()
        assert shutdown_event.is_set()


class TestHandleButtonInteractions:
    """Test cases for handle_button_interactions function."""
    
    def test_handle_button_interactions_long_press(self):
        """Test handling long press button action."""
        mock_task_interface = Mock()
        mock_task_interface.button_handler.check_button.return_value = ("long_press", True)
        
        with patch('hexapod.main.logger') as mock_logger:
            handle_button_interactions(mock_task_interface)
            
            mock_task_interface.sound_source_localization.assert_called_once()
            mock_logger.user_info.assert_called_with("Long press detected, starting sound source localization...")
    
    def test_handle_button_interactions_toggle_start(self):
        """Test handling toggle button action when starting system."""
        mock_task_interface = Mock()
        mock_task_interface.button_handler.check_button.return_value = ("toggle", True)
        
        with patch('hexapod.main.logger') as mock_logger, \
             patch('time.sleep'):
            handle_button_interactions(mock_task_interface)
            
            mock_task_interface.hexapod.move_to_position.assert_called_once_with(PredefinedPosition.LOW_PROFILE)
            mock_task_interface.request_unpause_voice_control.assert_called_once()
            mock_logger.user_info.assert_called_with("Starting system...")
    
    def test_handle_button_interactions_toggle_stop(self):
        """Test handling toggle button action when stopping system."""
        mock_task_interface = Mock()
        mock_task_interface.button_handler.check_button.return_value = ("toggle", False)
        
        with patch('hexapod.main.logger') as mock_logger, \
             patch('time.sleep'):
            handle_button_interactions(mock_task_interface)
            
            mock_task_interface.request_pause_voice_control.assert_called_once()
            mock_task_interface.hexapod.move_to_position.assert_called_once_with(PredefinedPosition.LOW_PROFILE)
            mock_task_interface.hexapod.deactivate_all_servos.assert_called_once()
            mock_logger.user_info.assert_called_with("Stopping system...")
    
    def test_handle_button_interactions_stop_task(self):
        """Test handling stop_task button action."""
        mock_task_interface = Mock()
        mock_task_interface.button_handler.check_button.return_value = ("stop_task", True)
        
        with patch('hexapod.main.logger') as mock_logger:
            handle_button_interactions(mock_task_interface)
            
            mock_task_interface.stop_task.assert_called_once()
            mock_task_interface.request_unblock_voice_control_pausing.assert_called_once()
            mock_task_interface.request_unpause_voice_control.assert_called_once()
            mock_logger.user_info.assert_called_with("Button pressed during blocking task, stopping current task...")
    
    def test_handle_button_interactions_no_action(self):
        """Test handling when no button action is detected."""
        mock_task_interface = Mock()
        mock_task_interface.button_handler.check_button.return_value = (None, False)
        
        with patch('hexapod.main.logger') as mock_logger:
            handle_button_interactions(mock_task_interface)
            
            # No methods should be called
            mock_task_interface.sound_source_localization.assert_not_called()
            mock_task_interface.hexapod.move_to_position.assert_not_called()
            mock_task_interface.request_unpause_voice_control.assert_not_called()
            mock_task_interface.request_pause_voice_control.assert_not_called()
            mock_task_interface.stop_task.assert_not_called()


class TestShutdownCleanup:
    """Test cases for shutdown_cleanup function."""
    
    def test_shutdown_cleanup_with_all_components(self):
        """Test shutdown cleanup with all components present."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_task_interface = Mock()
        
        with patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.threading.enumerate', return_value=[]):
            shutdown_cleanup(mock_voice_control, mock_manual_controller, mock_task_interface)
            
            mock_voice_control.stop.assert_called_once()
            mock_voice_control.join.assert_called_once()
            mock_manual_controller.stop.assert_called_once()
            mock_manual_controller.join.assert_called_once()
            mock_task_interface.cleanup.assert_called_once()
            mock_logger.critical.assert_called_with("Stopping all tasks and deactivating hexapod...")
            mock_logger.user_info.assert_called_with("Exiting...")
    
    def test_shutdown_cleanup_with_none_components(self):
        """Test shutdown cleanup with None components."""
        with patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.threading.enumerate', return_value=[]):
            shutdown_cleanup(None, None, Mock())
            
            mock_logger.critical.assert_called_with("Stopping all tasks and deactivating hexapod...")
            mock_logger.user_info.assert_called_with("Exiting...")
    
    def test_shutdown_cleanup_with_threads(self):
        """Test shutdown cleanup with active threads."""
        mock_thread = Mock()
        mock_thread.name = "TestThread"
        mock_thread.is_alive.return_value = True
        
        with patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.threading.enumerate', return_value=[mock_thread]):
            shutdown_cleanup(None, None, Mock())
            
            mock_logger.debug.assert_called_with("TestThread, True")


class TestCreateMainParser:
    """Test cases for create_main_parser function."""
    
    def test_create_main_parser(self):
        """Test creating main argument parser."""
        parser = create_main_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description == "Hexapod Voice Control System"
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter
    
    def test_parser_has_required_arguments(self):
        """Test that parser has all required arguments."""
        parser = create_main_parser()
        
        # Test parsing with all arguments
        args = parser.parse_args([
            '--access-key', 'test_key',
            '--log-level', 'DEBUG',
            '--log-dir', '/tmp/logs',
            '--clean',
            '--print-context'
        ])
        
        assert args.access_key == 'test_key'
        assert args.log_level == 'DEBUG'
        assert args.log_dir == Path('/tmp/logs')
        assert args.clean is True
        assert args.print_context is True
    
    def test_parser_default_values(self):
        """Test parser default values."""
        parser = create_main_parser()
        args = parser.parse_args([])
        
        assert args.access_key is None
        assert args.log_level == 'INFO'
        assert args.log_dir == Path('logs')
        assert args.clean is False
        assert args.print_context is False
    
    def test_parser_log_level_choices(self):
        """Test that log level choices are correct."""
        parser = create_main_parser()
        
        valid_levels = [
            "DEBUG", "INFO", "USER_INFO", "ODAS_USER_INFO", 
            "GAMEPAD_MODE_INFO", "WARNING", "ERROR", "CRITICAL"
        ]
        
        for level in valid_levels:
            args = parser.parse_args(['--log-level', level])
            assert args.log_level == level
    
    def test_parser_help_text(self):
        """Test that parser has correct help text."""
        parser = create_main_parser()
        help_text = parser.format_help()
        
        assert "Hexapod Voice Control System" in help_text
        assert "Example usage:" in help_text
        assert "--access-key" in help_text
        assert "--log-level" in help_text
        assert "--clean" in help_text


class TestCreateApplicationComponents:
    """Test cases for create_application_components function."""
    
    def test_create_application_components_basic(self):
        """Test creating application components with basic configuration."""
        mock_config = Mock()
        mock_config.get_picovoice_key.return_value = 'test_key'
        
        args = argparse.Namespace(
            clean=False,
            log_dir=Path('logs'),
            log_config_file=Path('config.yaml'),
            log_level='INFO',
            print_context=False
        )
        
        with patch('hexapod.main.clean_logs') as mock_clean_logs, \
             patch('hexapod.main.setup_logging') as mock_setup_logging, \
             patch('hexapod.main.TaskInterface') as mock_task_interface_class, \
             patch('hexapod.main.VoiceControl') as mock_voice_control_class, \
             patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.Path') as mock_path:
            
            mock_task_interface = Mock()
            mock_voice_control = Mock()
            mock_task_interface_class.return_value = mock_task_interface
            mock_voice_control_class.return_value = mock_voice_control
            mock_path.return_value.resolve.return_value.parent = Path('/test')
            
            task_interface, voice_control = create_application_components(mock_config, args)
            
            mock_clean_logs.assert_not_called()
            mock_setup_logging.assert_called_once()
            mock_task_interface_class.assert_called_once()
            mock_voice_control_class.assert_called_once()
            mock_task_interface.set_voice_control.assert_called_once_with(mock_voice_control)
            mock_task_interface.wake_up.assert_called_once()
            mock_voice_control.print_context_info.assert_not_called()
    
    def test_create_application_components_with_clean(self):
        """Test creating application components with clean flag."""
        mock_config = Mock()
        mock_config.get_picovoice_key.return_value = 'test_key'
        
        args = argparse.Namespace(
            clean=True,
            log_dir=Path('logs'),
            log_config_file=Path('config.yaml'),
            log_level='INFO',
            print_context=False
        )
        
        with patch('hexapod.main.clean_logs') as mock_clean_logs, \
             patch('hexapod.main.setup_logging'), \
             patch('hexapod.main.TaskInterface'), \
             patch('hexapod.main.VoiceControl'), \
             patch('hexapod.main.logger'), \
             patch('hexapod.main.Path'):
            
            create_application_components(mock_config, args)
            
            mock_clean_logs.assert_called_once()
    
    def test_create_application_components_with_print_context(self):
        """Test creating application components with print context flag."""
        mock_config = Mock()
        mock_config.get_picovoice_key.return_value = 'test_key'
        
        args = argparse.Namespace(
            clean=False,
            log_dir=Path('logs'),
            log_config_file=Path('config.yaml'),
            log_level='INFO',
            print_context=True
        )
        
        with patch('hexapod.main.clean_logs'), \
             patch('hexapod.main.setup_logging'), \
             patch('hexapod.main.TaskInterface'), \
             patch('hexapod.main.VoiceControl') as mock_voice_control_class, \
             patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.Path'):
            
            mock_voice_control = Mock()
            mock_voice_control_class.return_value = mock_voice_control
            
            create_application_components(mock_config, args)
            
            mock_voice_control.print_context_info.assert_called_once()
            mock_logger.debug.assert_called_with("Print context flag detected, printing context")


class TestInitializeManualController:
    """Test cases for initialize_manual_controller function."""
    
    def test_initialize_manual_controller_success(self):
        """Test successful manual controller initialization."""
        mock_task_interface = Mock()
        mock_voice_control = Mock()
        mock_config = Mock()
        args = argparse.Namespace()
        
        with patch('hexapod.main.GamepadHexapodController') as mock_controller_class, \
             patch('hexapod.main.logger') as mock_logger:
            
            mock_controller = Mock()
            mock_controller_class.return_value = mock_controller
            
            result = initialize_manual_controller(mock_task_interface, mock_voice_control, mock_config, args)
            
            mock_task_interface.request_pause_voice_control.assert_called_once()
            mock_controller_class.assert_called_once_with(
                task_interface=mock_task_interface,
                voice_control=mock_voice_control,
                shutdown_callback=shutdown_callback
            )
            mock_controller.start.assert_called_once()
            mock_logger.user_info.assert_called_with("Manual controller started successfully")
            assert result == mock_controller
    
    def test_initialize_manual_controller_failure(self):
        """Test manual controller initialization failure."""
        mock_task_interface = Mock()
        mock_voice_control = Mock()
        mock_config = Mock()
        args = argparse.Namespace()
        
        with patch('hexapod.main.GamepadHexapodController') as mock_controller_class, \
             patch('hexapod.main.logger') as mock_logger:
            
            mock_controller_class.side_effect = Exception("Controller error")
            
            result = initialize_manual_controller(mock_task_interface, mock_voice_control, mock_config, args)
            
            mock_task_interface.request_pause_voice_control.assert_called_once()
            mock_task_interface.request_unpause_voice_control.assert_called_once()
            mock_logger.warning.assert_called_with("Failed to initialize manual controller: Controller error")
            mock_logger.user_info.assert_called_with("Falling back to voice control mode")
            assert result is None


class TestRunMainLoop:
    """Test cases for run_main_loop function."""
    
    def setup_method(self):
        """Setup method to ensure clean state before each test."""
        from hexapod.main import shutdown_event
        shutdown_event.clear()
    
    def teardown_method(self):
        """Teardown method to ensure clean state after each test."""
        from hexapod.main import shutdown_event
        shutdown_event.clear()
    
    def test_run_main_loop_with_shutdown_event(self):
        """Test main loop with shutdown event triggered."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_task_interface = Mock()
        
        # Set the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.set()
        
        with patch('hexapod.main.shutdown_cleanup') as mock_cleanup, \
             patch('hexapod.main.logger') as mock_logger:
            
            run_main_loop(mock_voice_control, mock_manual_controller, mock_task_interface)
            
            mock_cleanup.assert_called_once_with(mock_voice_control, mock_manual_controller, mock_task_interface)
            mock_logger.critical.assert_called_with("Shutdown event detected, initiating shutdown")
    
    def test_run_main_loop_with_manual_controller_voice_mode(self):
        """Test main loop with manual controller in voice control mode."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_manual_controller.current_mode = mock_manual_controller.VOICE_CONTROL_MODE
        mock_task_interface = Mock()
        
        # Clear the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.clear()
        
        with patch('hexapod.main.handle_button_interactions') as mock_handle_buttons, \
             patch('hexapod.main.time.sleep') as mock_sleep:
            
            # Use side_effect to control the loop and exit after one iteration
            def side_effect(*args, **kwargs):
                shutdown_event.set()  # Set the event to exit the loop
                return None
            
            mock_sleep.side_effect = side_effect
            
            run_main_loop(mock_voice_control, mock_manual_controller, mock_task_interface)
            
            mock_handle_buttons.assert_called_once_with(mock_task_interface)
            mock_sleep.assert_called_with(0.1)
    
    def test_run_main_loop_with_manual_controller_other_mode(self):
        """Test main loop with manual controller in other mode."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_manual_controller.current_mode = "other_mode"
        mock_task_interface = Mock()
        
        # Clear the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.clear()
        
        with patch('hexapod.main.handle_button_interactions') as mock_handle_buttons, \
             patch('hexapod.main.time.sleep') as mock_sleep:
            
            # Use side_effect to control the loop and exit after one iteration
            def side_effect(*args, **kwargs):
                shutdown_event.set()  # Set the event to exit the loop
                return None
            
            mock_sleep.side_effect = side_effect
            
            run_main_loop(mock_voice_control, mock_manual_controller, mock_task_interface)
            
            mock_handle_buttons.assert_not_called()
            mock_sleep.assert_called_with(0.1)
    
    def test_run_main_loop_without_manual_controller(self):
        """Test main loop without manual controller."""
        mock_voice_control = Mock()
        mock_task_interface = Mock()
        
        # Clear the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.clear()
        
        with patch('hexapod.main.handle_button_interactions') as mock_handle_buttons, \
             patch('hexapod.main.time.sleep') as mock_sleep:
            
            # Use side_effect to control the loop and exit after one iteration
            def side_effect(*args, **kwargs):
                shutdown_event.set()  # Set the event to exit the loop
                return None
            
            mock_sleep.side_effect = side_effect
            
            run_main_loop(mock_voice_control, None, mock_task_interface)
            
            mock_handle_buttons.assert_called_once_with(mock_task_interface)
            # Check that sleep was called with 0.1 (the main loop sleep)
            sleep_calls = [call for call in mock_sleep.call_args_list if call[0][0] == 0.1]
            assert len(sleep_calls) >= 1, f"Expected sleep(0.1) call, but got calls: {mock_sleep.call_args_list}"
    
    def test_run_main_loop_keyboard_interrupt(self):
        """Test main loop with KeyboardInterrupt."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_task_interface = Mock()
        
        # Clear the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.clear()
        
        with patch('hexapod.main.shutdown_cleanup') as mock_cleanup, \
             patch('hexapod.main.logger') as mock_logger, \
             patch('hexapod.main.time.sleep') as mock_sleep, \
             patch('hexapod.main.sys.stdout.write') as mock_stdout_write:
            
            mock_sleep.side_effect = KeyboardInterrupt()
            
            run_main_loop(mock_voice_control, mock_manual_controller, mock_task_interface)
            
            mock_cleanup.assert_called_once_with(mock_voice_control, mock_manual_controller, mock_task_interface)
            mock_logger.critical.assert_called_with("KeyboardInterrupt detected, initiating shutdown")
            mock_stdout_write.assert_called_with("\b" * 2)
    
    def test_run_main_loop_cleanup_in_finally(self):
        """Test main loop cleanup in finally block."""
        mock_voice_control = Mock()
        mock_manual_controller = Mock()
        mock_task_interface = Mock()
        
        # Clear the global shutdown event
        from hexapod.main import shutdown_event
        shutdown_event.clear()
        
        with patch('hexapod.main.shutdown_cleanup') as mock_cleanup, \
             patch('hexapod.main.time.sleep') as mock_sleep:
            
            # Simulate an exception that doesn't trigger cleanup
            mock_sleep.side_effect = Exception("Test exception")
            
            # The exception should be caught and cleanup should still happen
            try:
                run_main_loop(mock_voice_control, mock_manual_controller, mock_task_interface)
            except Exception:
                pass  # Expected exception
            
            # Should be called in finally block
            mock_cleanup.assert_called_once_with(mock_voice_control, mock_manual_controller, mock_task_interface)


class TestMainFunction:
    """Test cases for main function."""
    
    def test_main_success(self):
        """Test successful main function execution."""
        with patch('hexapod.main.create_main_parser') as mock_parser_func, \
             patch('hexapod.main.Config') as mock_config_class, \
             patch('hexapod.main.create_application_components') as mock_create_components, \
             patch('hexapod.main.initialize_manual_controller') as mock_init_controller, \
             patch('hexapod.main.run_main_loop') as mock_run_loop:
            
            # Setup mocks
            mock_parser = Mock()
            mock_args = Mock()
            mock_parser.parse_args.return_value = mock_args
            mock_parser_func.return_value = mock_parser
            
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            mock_task_interface = Mock()
            mock_voice_control = Mock()
            mock_create_components.return_value = (mock_task_interface, mock_voice_control)
            
            mock_manual_controller = Mock()
            mock_init_controller.return_value = mock_manual_controller
            
            # Call main
            main()
            
            # Verify calls
            mock_config_class.assert_called_once_with(config_file=mock_args.config)
            mock_config.update_from_args.assert_called_once_with(mock_args)
            mock_config.validate.assert_called_once()
            mock_create_components.assert_called_once_with(mock_config, mock_args)
            mock_voice_control.start.assert_called_once()
            mock_init_controller.assert_called_once_with(mock_task_interface, mock_voice_control, mock_config, mock_args)
            mock_run_loop.assert_called_once_with(mock_voice_control, mock_manual_controller, mock_task_interface)
    
    def test_main_config_validation_error(self):
        """Test main function with configuration validation error."""
        with patch('hexapod.main.create_main_parser') as mock_parser_func, \
             patch('hexapod.main.Config') as mock_config_class, \
             patch('hexapod.main.sys.exit') as mock_exit, \
             patch('hexapod.main.print') as mock_print, \
             patch('hexapod.main.create_application_components') as mock_create_components:
            
            # Setup mocks
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.config = Path('/test/config')
            mock_args.log_dir = Path('/test/logs')
            mock_args.log_config_file = Path('/test/log_config.yaml')
            mock_args.log_level = 'INFO'
            mock_args.clean = False
            mock_args.print_context = False
            mock_parser.parse_args.return_value = mock_args
            mock_parser_func.return_value = mock_parser
            
            mock_config = Mock()
            mock_config.validate.side_effect = ValueError("Config error")
            mock_config_class.return_value = mock_config
            
            # Make sys.exit actually raise SystemExit
            mock_exit.side_effect = SystemExit(1)
            
            # Call main and expect it to raise SystemExit
            with pytest.raises(SystemExit):
                main()
            
            # Verify error handling
            mock_config.update_from_args.assert_called_once_with(mock_args)
            mock_config.validate.assert_called_once()
            mock_print.assert_any_call("Configuration error: Config error")
            mock_print.assert_any_call("\nFor help with configuration, run: hexapod --help")
            mock_print.assert_any_call("For installation and setup instructions, see: INSTALL.md")
            mock_exit.assert_called_once_with(1)
            # create_application_components should not be called when validation fails
            mock_create_components.assert_not_called()
