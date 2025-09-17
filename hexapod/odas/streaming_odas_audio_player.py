#!/usr/bin/env python3

"""
ODAS Remote Audio Player

This script monitors continuous audio streams from ODAS on a remote machine, transfers them to the local machine,
and plays them in real-time. By default, it plays the post-filtered audio stream, but can also handle separated audio streams.

ODAS creates two continuous raw audio streams:
1. postfiltered.raw: Contains post-filtered audio streams (default, optimized for listening)
2. separated.raw: Contains separated audio streams (one for each sound source)

The script continuously monitors these streams, transfers new audio data, and plays it in real-time.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import sys
import time
import tempfile
import platform
import subprocess
import threading
import logging
import logging.config
import argparse
from pathlib import Path

import paramiko
import sounddevice as sd
import wave
import numpy as np
import queue

from hexapod.interface import setup_logging, clean_logs

if TYPE_CHECKING:
    from typing import Optional, List

DEFAULT_HOST = "hexapod"
DEFAULT_HOSTNAME = "192.168.0.122"
DEFAULT_USER = "hexapod"
DEFAULT_SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
DEFAULT_REMOTE_DIR = "/home/hexapod/hexapod/data/audio/odas"
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 4
DEFAULT_BUFFER_SIZE = 1024
DEFAULT_CHECK_INTERVAL = 0.5

# Type aliases
AudioFileType = str  # 'postfiltered' or 'separated'
ProcessList = List[subprocess.Popen]

from hexapod.interface import get_custom_logger

logger = get_custom_logger("odas_logger")


class StreamingODASAudioPlayer:
    """
    A class to handle remote ODAS audio streaming and playback.

    This class manages the connection to a remote machine running ODAS,
    transfers audio data, and plays it locally in real-time.
    """

    def __init__(
        self,
        remote_host: str = DEFAULT_HOSTNAME,
        remote_user: str = DEFAULT_USER,
        remote_dir: str = DEFAULT_REMOTE_DIR,
        local_dir: str = "data/audio/odas/streaming",
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
        ssh_key_path: str = str(DEFAULT_SSH_KEY),
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        check_interval: float = DEFAULT_CHECK_INTERVAL,
    ) -> None:
        """
        Initialize the remote ODAS audio player.

        Args:
            remote_host (str): Hostname or IP of the remote machine
            remote_user (str): Username for SSH connection
            remote_dir (str): Directory on remote machine where ODAS creates raw files
            local_dir (str): Directory where WAV files will be saved locally
            sample_rate (int): Sample rate of the audio files
            channels (int): Number of channels in the audio files
            ssh_key_path (str): Path to SSH private key
            buffer_size (int): Size of audio buffer in bytes
            check_interval (float): Interval in seconds to check for new audio data
        """
        self.remote_host = remote_host
        self.remote_user = remote_user
        self.remote_dir = Path(remote_dir)
        self.local_dir = Path(local_dir)
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        self.check_interval = check_interval
        self.running = True
        self.processes: ProcessList = []
        self.ssh_key_path = ssh_key_path

        # Create local directory if it doesn't exist
        self.local_dir.mkdir(parents=True, exist_ok=True)

        # Set up SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Log directory information
        logger.user_info(f"Monitoring ODAS audio streams on {self.remote_host}")
        logger.user_info(f"Saving WAV files locally to: {self.local_dir}")

        self.audio_queue = queue.Queue()
        self.stream = None
        self.stream_thread = None
        self.is_playing = False

    def connect_ssh(self) -> None:
        """Establish SSH connection to remote host."""
        try:
            if self.ssh_key_path:
                self.ssh.connect(
                    self.remote_host,
                    username=self.remote_user,
                    key_filename=self.ssh_key_path,
                )
            else:
                self.ssh.connect(self.remote_host, username=self.remote_user)
            logger.user_info(f"Connected to {self.remote_host}")
        except Exception as e:
            logger.critical(f"Failed to connect to {self.remote_host}: {str(e)}")
            raise

    def transfer_file(self, remote_file: str, local_file: Path) -> None:
        """
        Transfer a file from remote to local machine using SFTP.

        Args:
            remote_file: Path to file on remote machine
            local_file: Path to save file locally
        """
        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_file, str(local_file))
            sftp.close()
            logger.debug(f"Transferred {remote_file} to {local_file}")
        except Exception as e:
            logger.warning(f"Error transferring {remote_file}: {str(e)}")
            raise

    def convert_to_wav(self, input_file: Path, output_file: Path) -> None:
        """
        Convert a raw audio file to WAV format using sox.

        Args:
            input_file: Path to the input raw file
            output_file: Path to the output WAV file
        """
        try:
            cmd = [
                "sox",
                "-r",
                str(self.sample_rate),
                "-b",
                "16",
                "-c",
                str(self.channels),
                "-e",
                "signed-integer",
                str(input_file),
                str(output_file),
            ]
            logger.debug(f"Converting {input_file} to {output_file}")
            subprocess.run(cmd, check=True)
            logger.debug(f"Successfully converted {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error converting {input_file}: {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error converting {input_file}: {str(e)}")

    def audio_callback(self, outdata, frames, time, status):
        """Callback for sounddevice streaming."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        try:
            data = self.audio_queue.get_nowait()
            outdata[:] = data.reshape(-1, 1)
        except queue.Empty:
            outdata.fill(0)
            if not self.is_playing:
                raise sd.CallbackStop()

    def start_audio_stream(self):
        """Start the audio streaming thread."""
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,  # Mono output
            callback=self.audio_callback,
            blocksize=1024,
        )
        self.stream.start()
        self.is_playing = True

    def stop_audio_stream(self):
        """Stop the audio streaming thread."""
        self.is_playing = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play_audio(self, wav_file: Path) -> None:
        """
        Process WAV file and add it to the audio queue for streaming playback.
        Splits audio into chunks that match the output buffer size.
        """
        try:
            # Read WAV file
            with wave.open(str(wav_file), "rb") as wav:
                # Get WAV parameters
                n_channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                frame_rate = wav.getframerate()
                n_frames = wav.getnframes()

                # Read all frames
                audio_data = wav.readframes(n_frames)

                # Convert to numpy array
                dtype = np.int16 if sample_width == 2 else np.int32
                audio_array = np.frombuffer(audio_data, dtype=dtype)

                # Reshape to channels
                audio_array = audio_array.reshape(-1, n_channels)

                # Mix down all channels (average them)
                audio_mono = np.mean(audio_array, axis=1)

                # Normalize audio for playback
                max_value = float(2 ** (sample_width * 8 - 1) - 1)
                audio_float = audio_mono.astype(np.float32) / max_value

                # Split audio into chunks that match the output buffer size
                chunk_size = 1024  # Must match blocksize in start_audio_stream
                for i in range(0, len(audio_float), chunk_size):
                    chunk = audio_float[i : i + chunk_size]
                    # Pad the last chunk if necessary
                    if len(chunk) < chunk_size:
                        chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                    self.audio_queue.put(chunk)

        except Exception as e:
            logger.warning(f"Error processing {wav_file}: {str(e)}")

    def stream_audio(self, file_type: AudioFileType) -> None:
        """
        Stream audio from remote machine and play it in real-time.
        """
        remote_file = str(self.remote_dir / f"{file_type}.raw")
        temp_file = Path(tempfile.mktemp(suffix=".raw"))
        wav_file = self.local_dir / f"{file_type}.wav"

        # Start audio stream
        self.start_audio_stream()

        while self.running:
            try:
                # Open SFTP connection
                sftp = self.ssh.open_sftp()

                # Get initial file size
                try:
                    file_size = sftp.stat(remote_file).st_size
                except FileNotFoundError:
                    logger.warning(
                        f"Audio stream {remote_file} not found on remote machine. Waiting for ODAS to start..."
                    )
                    time.sleep(1)
                    continue

                logger.user_info(f"Starting to stream {file_type} audio")

                while self.running:
                    try:
                        # Get current file size
                        current_size = sftp.stat(remote_file).st_size

                        if current_size > file_size:
                            # New audio data available
                            with sftp.open(remote_file, "rb") as remote:
                                remote.seek(file_size)
                                new_data = remote.read(current_size - file_size)

                                # Write new data to temporary file
                                with open(temp_file, "wb") as local:
                                    local.write(new_data)

                                # Convert to WAV and play
                                self.convert_to_wav(temp_file, wav_file)
                                self.play_audio(wav_file)

                                # Update file size
                                file_size = current_size

                        # Sleep for the configured interval
                        time.sleep(self.check_interval)

                    except FileNotFoundError:
                        logger.warning(f"ODAS stopped. Waiting for reconnection...")
                        break
                    except Exception as e:
                        logger.error(f"Error streaming {file_type} audio: {str(e)}")
                        time.sleep(1)

            except Exception as e:
                logger.error(f"Error in {file_type} stream: {str(e)}")
                time.sleep(1)
            finally:
                try:
                    sftp.close()
                    temp_file.unlink(missing_ok=True)
                except:
                    pass

    def monitor_files(self, file_type: AudioFileType = "separated") -> None:
        """
        Monitor and stream audio from ODAS based on the specified file type.

        Args:
            file_type: Type of audio file to monitor ('postfiltered' or 'separated')
        """
        logger.user_info(f"Starting to monitor ODAS audio streams (type: {file_type})")

        # Establish SSH connection first
        try:
            self.connect_ssh()
        except Exception as e:
            logger.critical(f"Failed to establish SSH connection: {str(e)}")
            return

        # Create and start streaming thread
        stream_thread = threading.Thread(
            target=self.stream_audio, args=(file_type,), daemon=True
        )
        stream_thread.start()
        stream_thread.join()

    def cleanup(self) -> None:
        """Clean up resources and terminate running processes."""
        logger.debug("Cleaning up...")

        # Stop audio stream
        self.stop_audio_stream()

        # Close SSH connection
        try:
            self.ssh.close()
        except:
            pass

        self.processes.clear()

    def get_audio_data(self) -> Optional[bytes]:
        """
        Get the latest audio data from ODAS.

        Returns:
            The latest audio data if available, None otherwise.
        """
        try:
            sftp = self.ssh.open_sftp()
            remote_file = str(self.remote_dir / "postfiltered.raw")

            try:
                current_size = sftp.stat(remote_file).st_size
            except FileNotFoundError:
                logger.warning("Audio stream not found on remote machine")
                return None

            if not hasattr(self, "_last_file_size"):
                self._last_file_size = current_size
                return None

            if current_size > self._last_file_size:
                with sftp.open(remote_file, "rb") as remote:
                    remote.seek(self._last_file_size)
                    new_data = remote.read(current_size - self._last_file_size)
                    self._last_file_size = current_size
                    return new_data

            return None

        except Exception as e:
            logger.error(f"Error getting audio data: {e}")
            return None
        finally:
            try:
                sftp.close()
            except:
                pass


def main() -> None:
    """Main entry point for the remote ODAS audio player."""

    # Add project paths for imports when run as script
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    src_path = project_root / "src"

    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))

    parser = argparse.ArgumentParser(description="Remote ODAS Audio Player")
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_HOSTNAME,
        help=f"Remote host address (default: {DEFAULT_HOSTNAME})",
    )
    parser.add_argument(
        "--user",
        type=str,
        default=DEFAULT_USER,
        help=f"Remote username (default: {DEFAULT_USER})",
    )
    parser.add_argument(
        "--remote-dir",
        type=str,
        default=DEFAULT_REMOTE_DIR,
        help=f"Remote directory containing ODAS audio files (default: {DEFAULT_REMOTE_DIR})",
    )
    parser.add_argument(
        "--local-dir",
        type=str,
        default="data/audio/odas/streaming",
        help="Local directory to store audio files (default: data/audio/odas/streaming)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help=f"Audio sample rate (default: {DEFAULT_SAMPLE_RATE})",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=DEFAULT_CHANNELS,
        help=f"Number of audio channels (default: {DEFAULT_CHANNELS})",
    )
    parser.add_argument(
        "--ssh-key",
        type=str,
        default=str(DEFAULT_SSH_KEY),
        help=f"Path to SSH private key (default: {DEFAULT_SSH_KEY})",
    )
    parser.add_argument(
        "--buffer-size",
        type=int,
        default=DEFAULT_BUFFER_SIZE,
        help=f"Buffer size for audio processing (default: {DEFAULT_BUFFER_SIZE})",
    )
    parser.add_argument(
        "--check-interval",
        type=float,
        default=DEFAULT_CHECK_INTERVAL,
        help=f"Interval in seconds to check for new audio data (default: {DEFAULT_CHECK_INTERVAL})",
    )
    parser.add_argument(
        "--file-type",
        type=str,
        choices=["postfiltered", "separated"],
        default="separated",
        help="Type of audio file to play: separated (default) or postfiltered",
    )
    parser.add_argument(
        "--log-dir", type=Path, default=Path("logs"), help="Directory to store logs"
    )
    parser.add_argument(
        "--log-config-file",
        type=Path,
        default=Path(__file__).parent.parent
        / "interface"
        / "logging"
        / "config"
        / "config.yaml",
        help="Path to log configuration file",
    )
    parser.add_argument(
        "--clean",
        "-c",
        action="store_true",
        help="Clean all logs in the logs directory.",
    )

    args = parser.parse_args()

    # Clean logs if requested
    if args.clean:
        clean_logs(args.log_dir)

    # Set up logging first
    setup_logging(log_dir=args.log_dir, config_file=args.log_config_file)

    logger.user_info("Starting ODAS Remote Audio Player")

    player = StreamingODASAudioPlayer(
        remote_host=args.host,
        remote_user=args.user,
        remote_dir=args.remote_dir,
        local_dir=args.local_dir,
        sample_rate=args.sample_rate,
        channels=args.channels,
        ssh_key_path=args.ssh_key,
        buffer_size=args.buffer_size,
        check_interval=args.check_interval,
    )

    try:
        player.monitor_files(file_type=args.file_type)
    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write("\b" * 2)
        logger.critical(
            "Stopping audio streaming and cleaning up due to keyboard interrupt..."
        )
    finally:
        player.cleanup()


if __name__ == "__main__":
    main()
