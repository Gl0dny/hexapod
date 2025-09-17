"""
StreamODASAudioTask

This module defines the StreamODASAudioTask class, which is responsible for
streaming audio from ODAS in real-time.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import threading
import time
import paramiko
from pathlib import Path

from hexapod.task_interface.tasks import Task
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler
    from hexapod.odas import ODASDoASSLProcessor

logger = get_custom_logger("task_interface_logger")


class StreamODASAudioTask(Task):
    """
    Task for streaming audio from ODAS in real-time.
    Extends sound source localization functionality to include audio streaming.
    """

    def __init__(
        self,
        hexapod: Hexapod,
        lights_handler: LightsInteractionHandler,
        odas_processor: ODASDoASSLProcessor,
        external_control_paused_event: threading.Event,
        stream_type: str = "separated",
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the StreamODASAudioTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            external_control_paused_event: Event to manage external control state.
            stream_type: Type of audio stream to play (default: "separated").
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing StreamODASAudioTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor
        self.external_control_paused_event = external_control_paused_event
        self.stream_type = stream_type
        self.odas_processor.stop_event = self.stop_event

        # Remote streaming configuration
        self.remote_host = "192.168.0.171"
        self.remote_user = "gl0dny"
        self.ssh_key_path = str(Path.home() / ".ssh" / "id_ed25519")
        self.remote_script_path = (
            "/Users/gl0dny/workspace/hexapod/src/odas/streaming_odas_audio_player.py"
        )
        self.ssh_client = None
        self.streaming_process = None

    def _initialize_odas_processor(self) -> None:
        """
        Initialize and start the ODAS processor.
        Handles the setup phase including starting the processor.
        """
        self.lights_handler.think()
        time.sleep(4)  # Wait for Voice Control to pause and release resources
        self.lights_handler.off()
        # Start ODAS processor
        self.odas_processor.start()

    def _cleanup_odas_processor(self) -> None:
        """
        Clean up ODAS processor resources.
        Ensures proper shutdown of the processor.
        """
        if hasattr(self, "odas_processor"):
            self.odas_processor.close()

    def _verify_ssh_connection(self) -> bool:
        """
        Verify SSH connection to remote host.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Test if host is reachable first
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.remote_host, 22))
            sock.close()

            if result != 0:
                logger.error(f"SSH port (22) is not open on {self.remote_host}")
                return False

            # Try to establish SSH connection
            test_client = paramiko.SSHClient()
            test_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            test_client.connect(
                self.remote_host,
                username=self.remote_user,
                key_filename=self.ssh_key_path,
                timeout=5,
            )
            test_client.close()
            return True

        except paramiko.AuthenticationException:
            logger.error(
                f"SSH authentication failed for {self.remote_user}@{self.remote_host}"
            )
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    def _start_remote_streaming(self) -> None:
        """
        Start the remote audio streaming process on the specified host.
        """
        try:
            # Verify SSH connection first
            if not self._verify_ssh_connection():
                raise Exception("SSH connection verification failed")

            # Initialize SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to remote host
            logger.info(f"Connecting to remote host {self.remote_host}")
            self.ssh_client.connect(
                self.remote_host,
                username=self.remote_user,
                key_filename=self.ssh_key_path,
                timeout=10,
            )

            # Verify script exists on remote host
            check_cmd = f"test -f {self.remote_script_path} && echo 'exists' || echo 'not found'"
            stdin, stdout, stderr = self.ssh_client.exec_command(check_cmd)
            result = stdout.read().decode().strip()

            if result != "exists":
                raise Exception(
                    f"Streaming script not found at {self.remote_script_path}"
                )

            # Construct command to run streaming script
            venv_path = "/Users/gl0dny/workspace/hexapod_venv"
            log_dir = "/Users/gl0dny/workspace/hexapod/logs/odas"
            log_file = f"{log_dir}/streaming.log"

            # Create log directory if it doesn't exist
            mkdir_cmd = f"mkdir -p {log_dir}"
            self.ssh_client.exec_command(mkdir_cmd)

            cmd = f"""
            source {venv_path}/bin/activate && 
            python3 {self.remote_script_path} --file-type {self.stream_type} > {log_file} 2>&1
            """
            logger.info(f"Starting remote streaming with command: {cmd}")

            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(f"bash -c '{cmd}'")
            self.streaming_process = (stdin, stdout, stderr)

            # Check for immediate errors
            error = stderr.read().decode()
            if error:
                logger.error(f"Error starting remote streaming: {error}")
                raise Exception(f"Failed to start remote streaming: {error}")

            logger.info("Remote streaming started successfully")

        except Exception as e:
            logger.error(f"Failed to start remote streaming: {e}")
            self._cleanup_remote_streaming()
            raise

    def _cleanup_remote_streaming(self) -> None:
        """
        Clean up remote streaming resources.
        """
        try:
            if self.ssh_client:
                # Get the log output
                log_cmd = "cat /Users/gl0dny/workspace/hexapod/logs/odas/streaming.log 2>/dev/null || true"
                stdin, stdout, stderr = self.ssh_client.exec_command(log_cmd)
                log_output = stdout.read().decode()
                if log_output:
                    logger.info(f"Streaming process log output:\n{log_output}")

                self.ssh_client.close()
                self.ssh_client = None

        except Exception as e:
            logger.error(f"Error during remote streaming cleanup: {e}")

    def _check_streaming_status(self) -> bool:
        """
        Check if the streaming process is still running.

        Returns:
            bool: True if process is running, False otherwise
        """
        try:
            if not self.ssh_client:
                return False

            # Check if the process is still running by checking the log file
            check_cmd = "ps aux | grep streaming_odas_audio_player | grep -v grep"
            stdin, stdout, stderr = self.ssh_client.exec_command(check_cmd)
            output = stdout.read().decode().strip()

            return bool(output)

        except Exception as e:
            logger.error(f"Error checking streaming status: {e}")
            return False

    @override
    def execute_task(self) -> None:
        """
        Streams audio from ODAS while maintaining sound source localization functionality.
        """
        logger.info("StreamODASAudioTask started")
        try:
            # Start ODAS processor initialization in a separate thread
            odas_thread = threading.Thread(target=self._initialize_odas_processor)
            odas_thread.start()

            # Start remote streaming
            self._start_remote_streaming()

            # Wait for the task to complete or be stopped
            while not self.stop_event.is_set():
                self.stop_event.wait(0.1)

        except Exception as e:
            logger.exception(f"ODAS audio streaming task failed: {e}")
        finally:
            self._cleanup_remote_streaming()
            self._cleanup_odas_processor()
            logger.info("StreamODASAudioTask completed")
