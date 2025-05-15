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

import os
import time
import subprocess
import threading
from pathlib import Path
import logging
import argparse
from datetime import datetime
import paramiko
import tempfile
import platform
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("odas_remote_audio")

# Default values from SSH config
DEFAULT_HOST = "hexapod"
DEFAULT_HOSTNAME = "192.168.0.122"
DEFAULT_USER = "hexapod"
DEFAULT_SSH_KEY = str(Path.home() / ".ssh" / "id_ed25519")
DEFAULT_REMOTE_DIR = "/home/hexapod/hexapod/src/odas"

class RemoteODASAudioPlayer:
    def __init__(self, remote_host: str = DEFAULT_HOSTNAME, remote_user: str = DEFAULT_USER, 
                 remote_dir: str = DEFAULT_REMOTE_DIR, local_dir: str = "logs/odas/audio", 
                 sample_rate: int = 44100, channels: int = 4, 
                 ssh_key_path: str = DEFAULT_SSH_KEY, buffer_size: int = 1024,
                 check_interval: float = 0.5):
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
        self.processes = []
        self.ssh_key_path = ssh_key_path
        
        # Create local directory if it doesn't exist
        self.local_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Log directory information
        logger.info(f"Monitoring ODAS audio streams on {self.remote_host}")
        logger.info(f"Saving WAV files locally to: {self.local_dir}")
        
        # Set up signal handler
        self.setup_signal_handler()

    def setup_signal_handler(self):
        """Set up signal handler for graceful shutdown."""
        import signal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()

    def connect_ssh(self):
        """Establish SSH connection to remote host."""
        try:
            if self.ssh_key_path:
                self.ssh.connect(
                    self.remote_host,
                    username=self.remote_user,
                    key_filename=self.ssh_key_path
                )
            else:
                self.ssh.connect(
                    self.remote_host,
                    username=self.remote_user
                )
            logger.info(f"Connected to {self.remote_host}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.remote_host}: {str(e)}")
            raise

    def transfer_file(self, remote_file: str, local_file: Path):
        """
        Transfer a file from remote to local machine using SFTP.

        Args:
            remote_file (str): Path to file on remote machine
            local_file (Path): Path to save file locally
        """
        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_file, str(local_file))
            sftp.close()
            logger.info(f"Transferred {remote_file} to {local_file}")
        except Exception as e:
            logger.error(f"Error transferring {remote_file}: {str(e)}")
            raise

    def convert_to_wav(self, input_file: Path, output_file: Path):
        """
        Convert a raw audio file to WAV format using sox.

        Args:
            input_file (Path): Path to the input raw file
            output_file (Path): Path to the output WAV file
        """
        try:
            cmd = [
                "sox",
                "-r", str(self.sample_rate),
                "-b", "16",
                "-c", str(self.channels),
                "-e", "signed-integer",
                str(input_file),
                str(output_file)
            ]
            logger.info(f"Converting {input_file} to {output_file}")
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully converted {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting {input_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error converting {input_file}: {str(e)}")

    def play_audio(self, wav_file: Path):
        """
        Play a WAV file using a suitable audio player.

        Args:
            wav_file (Path): Path to the WAV file to play
        """
        try:
            # Use afplay on macOS, aplay on Linux
            if platform.system() == 'Darwin':  # macOS
                player = "afplay"
            else:  # Linux
                player = "aplay"
                
            cmd = [player, str(wav_file)]
            process = subprocess.Popen(cmd)
            self.processes.append(process)
            logger.info(f"Playing {wav_file} using {player}")
        except Exception as e:
            logger.error(f"Error playing {wav_file}: {str(e)}")

    def stream_audio(self, file_type: str):
        """
        Stream audio from remote machine and play it in real-time.

        Args:
            file_type (str): Type of audio stream ('separated' or 'postfiltered')
        """
        remote_file = str(self.remote_dir / f"{file_type}.raw")
        temp_file = Path(tempfile.mktemp(suffix='.raw'))
        wav_file = self.local_dir / f"{file_type}.wav"
        
        while self.running:
            try:
                # Open SFTP connection
                sftp = self.ssh.open_sftp()
                
                # Get initial file size
                try:
                    file_size = sftp.stat(remote_file).st_size
                except FileNotFoundError:
                    logger.warning(f"Audio stream {remote_file} not found on remote machine. Waiting for ODAS to start...")
                    time.sleep(1)
                    continue
                
                logger.info(f"Starting to stream {file_type} audio")
                
                while self.running:
                    try:
                        # Get current file size
                        current_size = sftp.stat(remote_file).st_size
                        
                        if current_size > file_size:
                            # New audio data available
                            with sftp.open(remote_file, 'rb') as remote:
                                remote.seek(file_size)
                                new_data = remote.read(current_size - file_size)
                                
                                # Write new data to temporary file
                                with open(temp_file, 'wb') as local:
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

    def monitor_files(self, file_type: str = 'postfiltered'):
        """Monitor and stream audio from ODAS based on the specified file type."""
        logger.info(f"Starting to monitor ODAS audio streams (type: {file_type})")
        
        # Establish SSH connection first
        try:
            self.connect_ssh()
        except Exception as e:
            logger.error(f"Failed to establish SSH connection: {str(e)}")
            return
        
        threads = []
        
        if file_type in ['postfiltered', 'both']:
            postfiltered_thread = threading.Thread(
                target=self.stream_audio,
                args=('postfiltered',),
                daemon=True
            )
            threads.append(postfiltered_thread)
            postfiltered_thread.start()
        
        if file_type in ['separated', 'both']:
            separated_thread = threading.Thread(
                target=self.stream_audio,
                args=('separated',),
                daemon=True
            )
            threads.append(separated_thread)
            separated_thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def cleanup(self):
        """Clean up resources and terminate running processes."""
        logger.info("Cleaning up...")
        
        # Terminate all running processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                try:
                    process.kill()
                except:
                    pass
        
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
            Optional[bytes]: The latest audio data if available, None otherwise.
        """
        try:
            sftp = self.ssh.open_sftp()
            remote_file = str(self.remote_dir / "postfiltered.raw")
            
            try:
                current_size = sftp.stat(remote_file).st_size
            except FileNotFoundError:
                logger.warning("Audio stream not found on remote machine")
                return None
                
            if not hasattr(self, '_last_file_size'):
                self._last_file_size = current_size
                return None
                
            if current_size > self._last_file_size:
                with sftp.open(remote_file, 'rb') as remote:
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

def main():
    """Main entry point for the remote ODAS audio player."""
    parser = argparse.ArgumentParser(description='Remote ODAS Audio Player')
    parser.add_argument('--host', type=str, default=DEFAULT_HOSTNAME,
                        help=f'Remote host address (default: {DEFAULT_HOSTNAME})')
    parser.add_argument('--user', type=str, default=DEFAULT_USER,
                        help=f'Remote username (default: {DEFAULT_USER})')
    parser.add_argument('--remote-dir', type=str, default=DEFAULT_REMOTE_DIR,
                        help=f'Remote directory containing ODAS audio files (default: {DEFAULT_REMOTE_DIR})')
    parser.add_argument('--local-dir', type=str, default='logs/odas/audio_output',
                        help='Local directory to store audio files (default: logs/odas/audio)')
    parser.add_argument('--sample-rate', type=int, default=44100,
                        help='Audio sample rate (default: 44100)')
    parser.add_argument('--channels', type=int, default=4,
                        help='Number of audio channels (default: 4)')
    parser.add_argument('--ssh-key', type=str, default=DEFAULT_SSH_KEY,
                        help=f'Path to SSH private key (default: {DEFAULT_SSH_KEY})')
    parser.add_argument('--buffer-size', type=int, default=1024,
                        help='Buffer size for audio processing (default: 1024)')
    parser.add_argument('--check-interval', type=float, default=0.5,
                        help='Interval in seconds to check for new audio data (default: 0.5)')
    parser.add_argument('--file-type', type=str, choices=['postfiltered', 'separated', 'both'], default='postfiltered',
                        help='Type of audio file to play: postfiltered (default), separated, or both')

    args = parser.parse_args()

    player = RemoteODASAudioPlayer(
        remote_host=args.host,
        remote_user=args.user,
        remote_dir=args.remote_dir,
        local_dir=args.local_dir,
        sample_rate=args.sample_rate,
        channels=args.channels,
        ssh_key_path=args.ssh_key,
        buffer_size=args.buffer_size,
        check_interval=args.check_interval
    )

    try:
        player.monitor_files(file_type=args.file_type)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Cleaning up...")
    finally:
        player.cleanup()

if __name__ == "__main__":
    main() 