#!/usr/bin/env python3

"""
ODAS (Open embeddeD Audition System) DoA/SSL Processor Implementation
Handles Direction of Arrival (DoA) and Sound Source Localization (SSL) data processing and visualization.
"""

import socket
import struct
import json
import time
import threading
from datetime import datetime
import signal
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, TextIO, Any, Dict, Tuple
import argparse
import sys
import math

current_file = Path(__file__)
src_dir = str(current_file.parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from lights import LightsInteractionHandler
from lights.animations.direction_of_arrival_animation import DirectionOfArrivalAnimation

logger = logging.getLogger("odas")

class ODASDoASSLProcessor:
    """
    ODAS DoA (Direction of Arrival) and SSL (Sound Source Localization) processor implementation.
    Handles sound source tracking, processing, and visualization.
    """

    def __init__(
        self,
        lights_handler: LightsInteractionHandler,
        mode: str = 'local',
        host: str = '192.168.0.171',
        tracked_port: int = 9000,
        potential_port: int = 9001,
        forward_to_gui: bool = False,
        debug_mode: bool = False
    ) -> None:
        """
        Initialize the ODAS server with configuration parameters.

        Args:
            lights_handler (LightsInteractionHandler): The lights handler to use for visualization.
            mode (str): Operation mode ('local' or 'remote').
            host (str): Host IP address for remote mode.
            tracked_port (int): Port for tracked sources.
            potential_port (int): Port for potential sources.
            forward_to_gui (bool): Whether to forward data to GUI.
            debug_mode (bool): Whether to enable debug mode.
        """
        self.mode: str = mode.lower()
        if self.mode == 'local':
            self.host: str = '127.0.0.1'
        else:
            self.host: str = host
        self.tracked_port: int = tracked_port
        self.potential_port: int = potential_port
        self.tracked_server: Optional[socket.socket] = None
        self.potential_server: Optional[socket.socket] = None
        self.tracked_client: Optional[socket.socket] = None
        self.potential_client: Optional[socket.socket] = None
        self.running: bool = True
        self.threads: List[threading.Thread] = []
        self.log_files: List[TextIO] = []
        self.odas_process: Optional[subprocess.Popen] = None
        self.forward_to_gui: bool = forward_to_gui
        self.gui_tracked_socket: Optional[socket.socket] = None
        self.gui_potential_socket: Optional[socket.socket] = None
        self.gui_host: str = "192.168.0.102"
        self.gui_tracked_port: int = 9000
        self.gui_potential_port: int = 9001

        # Create base logs directory
        workspace_root: Path = Path(__file__).parent.parent.parent
        self.base_logs_dir: Path = workspace_root / "logs" / "odas" / "ssl"
        try:
            self.base_logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory: {str(e)}")
            self.base_logs_dir = Path(__file__).parent

        # Create log files
        self.tracked_log: TextIO = self._open_log_file(self.base_logs_dir / "tracked.log")
        self.potential_log: TextIO = self._open_log_file(self.base_logs_dir / "potential.log")

        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Initialize LED visualization using the provided lights handler
        self.lights_handler = lights_handler
        self.doa_animation = DirectionOfArrivalAnimation(self.lights_handler.lights)
        self.tracked_sources: Dict[int, Dict] = {}
        self.potential_sources: Dict[int, Dict] = {}
        self.sources_lock: threading.Lock = threading.Lock()

        # Status tracking variables
        self.last_active_source_time: float = time.time()
        self.current_active_sources: int = 0
        self.last_inactive_time: Optional[float] = None
        self.last_status_message_time: Optional[float] = None
        self.status_lock: threading.Lock = threading.Lock()

        # Debug mode and display control
        self.debug_mode: bool = debug_mode
        self.last_num_lines: int = 0  # Track number of lines printed last update
        self.initial_connection_made: bool = False

    def _open_log_file(self, path: Path) -> TextIO:
        """Open a log file and add it to the list of managed log files."""
        try:
            log_file: TextIO = open(path, "w")
            self.log_files.append(log_file)
            return log_file
        except Exception as e:
            print(f"Error creating log file: {str(e)}")
            class DummyFile:
                def write(self, *args: Any, **kwargs: Any) -> None: pass
                def flush(self, *args: Any, **kwargs: Any) -> None: pass
                def close(self, *args: Any, **kwargs: Any) -> None: pass
            return DummyFile()

    def signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals (SIGINT, SIGTERM)."""
        print(f"\nShutting down...")
        self.running = False

    def log(self, message: str, log_file: Optional[TextIO] = None, print_to_console: bool = False) -> None:
        """Log a message to console and optionally to a specific log file."""
        if not self.running:
            return
        
        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message: str = f"[{timestamp}] {message}\n"
        
        if print_to_console:
            print(log_message, end='')
        
        try:
            if log_file:
                log_file.write(log_message)
                log_file.flush()
        except:
            pass

    def start_server(self, port: int) -> socket.socket:
        """Start a TCP server on the specified port."""
        server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, port))
        server_socket.listen(1)
        if not self.initial_connection_made:
            print(f"Listening on {self.host}:{port}")
            self.initial_connection_made = True
        return server_socket

    def connect_to_gui(self) -> None:
        """Connect to the remote GUI station."""
        try:
            self.gui_tracked_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.gui_tracked_socket.connect((self.gui_host, self.gui_tracked_port))
            self.gui_potential_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.gui_potential_socket.connect((self.gui_host, self.gui_potential_port))
            print(f"Connected to GUI at {self.gui_host}")
        except Exception as e:
            print(f"GUI connection error: {str(e)}")
            print("Disabling GUI forwarding...")
            self.forward_to_gui = False
            if self.gui_tracked_socket:
                self.gui_tracked_socket.close()
                self.gui_tracked_socket = None
            if self.gui_potential_socket:
                self.gui_potential_socket.close()
                self.gui_potential_socket = None

    def forward_data_to_gui(self, data: bytes, client_type: str) -> None:
        """Forward data to the GUI station."""
        try:
            if client_type == "tracked" and self.gui_tracked_socket:
                self.gui_tracked_socket.send(data)
            elif client_type == "potential" and self.gui_potential_socket:
                self.gui_potential_socket.send(data)
        except (BrokenPipeError, ConnectionResetError):
            print("GUI connection lost. Attempting to reconnect...")
            self._handle_gui_disconnection()
        except Exception as e:
            print(f"GUI forward error: {str(e)}")

    def _handle_gui_disconnection(self) -> None:
        """Handle GUI disconnection by attempting to reconnect or disabling forwarding."""
        try:
            # Close existing sockets
            if self.gui_tracked_socket:
                self.gui_tracked_socket.close()
                self.gui_tracked_socket = None
            if self.gui_potential_socket:
                self.gui_potential_socket.close()
                self.gui_potential_socket = None

            # Attempt to reconnect
            self.connect_to_gui()
        except Exception as e:
            print(f"Failed to reconnect to GUI: {str(e)}")
            print("Disabling GUI forwarding...")
            self.forward_to_gui = False

    def _get_direction(self, x: float, y: float, z: float) -> str:
        """Calculate the estimated direction based on x, y, z coordinates."""
        azimuth = math.degrees(math.atan2(y, x))
        azimuth = (azimuth + 360) % 360
        directions = ['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE']
        index = round(azimuth / 45) % 8
        return directions[index]

    def _print_debug_info(self, active_sources: Dict[int, Dict]) -> None:
        """Print active sources in a multi-line format that updates in-place."""
        if not self.debug_mode:
            return

        current_lines = len(active_sources)
        
        # Move up to start of block
        if self.last_num_lines > 0:
            print(f"\033[{self.last_num_lines}A", end='', flush=True)

        # Clear all previous lines in the block
        for _ in range(self.last_num_lines):
            print("\033[K", flush=True)  # Clear the line and move down
            
        # Move back to the top of the block
        if self.last_num_lines > 0:
            print(f"\033[{self.last_num_lines}A", end='', flush=True)
        
        if current_lines == 0:
            # Print "no sources" message
            print("\033[KNo sources tracked", flush=True)
            self.last_num_lines = 1
        else:
            
            for sid, src in active_sources.items():
                x = src.get('x', 0)
                y = src.get('y', 0)
                z = src.get('z', 0)
                activity = src.get('activity', 0)
                direction = self._get_direction(x, y, z)
                print(f"\033[KSource {sid}: ({x:.2f}, {y:.2f}, {z:.2f}) | {direction} | Act:{activity:.2f}", flush=True)
            self.last_num_lines = current_lines

    def handle_client(self, client_socket: socket.socket, client_type: str) -> None:
        """Handle data from a connected client."""
        log_file: TextIO = self.tracked_log if client_type == "tracked" else self.potential_log
        
        while self.running:
            try:
                client_socket.settimeout(1.0)
                size_bytes: bytes = client_socket.recv(4)
                if not size_bytes:
                    break

                size: int = struct.unpack('I', size_bytes)[0]
                data: bytes = client_socket.recv(size)
                if not data:
                    break

                if self.forward_to_gui:
                    self.forward_data_to_gui(size_bytes + data, client_type)

                try:
                    json_str = data.decode('utf-8')
                    json_objects = []
                    start = 0
                    
                    while True:
                        start_brace = json_str.find('{', start)
                        if start_brace == -1:
                            break
                        end_brace = json_str.find('}', start_brace)
                        if end_brace == -1:
                            break
                        json_obj = json_str[start_brace:end_brace+1]
                        if json_obj:
                            json_objects.append(json_obj)
                            start = end_brace
                        else:
                            break
                    
                    all_sources: Dict[int, Dict] = {}
                    
                    for json_obj in json_objects:
                        try:
                            source_data = json.loads(json_obj)
                            
                            if client_type == "tracked":
                                source_id = source_data.get('id', 0)
                                if source_id > 0:
                                    all_sources[source_id] = source_data
                            else:
                                source_id = len(self.potential_sources)
                                with self.sources_lock:
                                    self.potential_sources[source_id] = source_data
                                self.log(f"Potential source detected:", log_file)
                                self.log(json.dumps(source_data, indent=2), log_file)
                            
                        except json.JSONDecodeError as e:
                            continue
                    
                    if client_type == "tracked":
                        if len(all_sources) > 4:
                            sorted_sources = sorted(all_sources.items(), 
                                                 key=lambda x: x[1].get('activity', 0), 
                                                 reverse=True)[:4]
                            active_sources = dict(sorted_sources)
                        else:
                            active_sources = all_sources
                        
                        current_active_sources = len(active_sources)
                        
                        with self.sources_lock:
                            self.tracked_sources = active_sources
                        
                        with self.status_lock:
                            self.last_active_source_time = time.time()
                            self.current_active_sources = current_active_sources
                            self.last_inactive_time = None
                            self.last_status_message_time = None
                        
                        if self.debug_mode:
                            self._print_debug_info(active_sources)
                    
                    with self.sources_lock:
                        tracked_sources_copy = dict(self.tracked_sources)
                        potential_sources_copy = dict(self.potential_sources)
                    self.doa_animation.update_sources(tracked_sources_copy)
                    
                except Exception as e:
                    continue
                    
            except socket.timeout:
                continue
            except (ConnectionResetError, BrokenPipeError):
                break
            except Exception as e:
                if self.running:
                    self.log(f"Client handler error: {str(e)}", log_file)
                break

    def _status_check_thread(self) -> None:
        """Thread that periodically checks and logs the status of tracked sources."""
        while self.running:
            try:
                current_time = time.time()
                with self.status_lock:
                    if self.current_active_sources == 0 and self.last_inactive_time is not None:
                        inactive_duration = current_time - self.last_inactive_time
                        if inactive_duration >= 15 and (self.last_status_message_time is None or 
                                                      current_time - self.last_status_message_time >= 15):
                            self.last_status_message_time = current_time
                time.sleep(1)
            except Exception as e:
                if self.running:
                    self.log(f"Status thread error: {str(e)}", self.tracked_log)
                time.sleep(1)

    def accept_connection(self, server_socket: socket.socket, client_type: str) -> Optional[socket.socket]:
        """Accept a connection from a client."""
        try:
            server_socket.settimeout(1.0)
            client_socket, address = server_socket.accept()
            return client_socket
        except socket.timeout:
            return None
        except Exception as e:
            if self.running:
                self.log(f"Accept error: {str(e)}")
            return None

    def start_odas_process(self) -> None:
        """Start the ODAS process in local mode."""
        if self.mode != 'local':
            return

        try:
            config_path = Path(__file__).parent / "config" / "local_odas.cfg"
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            self.odas_process = subprocess.Popen(
                ["odas", "-c", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            threading.Thread(target=self._monitor_odas_output, daemon=True).start()
            
        except Exception as e:
            print(f"ODAS start error: {str(e)}")
            self.running = False

    def _monitor_odas_output(self) -> None:
        """Monitor the ODAS process output and log it."""
        if not self.odas_process:
            return

        try:
            while self.running and self.odas_process.poll() is None:
                stdout = self.odas_process.stdout.readline() if self.odas_process.stdout else None
                stderr = self.odas_process.stderr.readline() if self.odas_process.stderr else None

                if stdout:
                    print(f"ODAS: {stdout.strip()}")
                if stderr:
                    print(f"ODAS Error: {stderr.strip()}")

        except Exception as e:
            print(f"ODAS monitor error: {str(e)}")

    def start(self) -> None:
        """Start the ODAS DoA/SSL processor."""
        try:
            if self.mode == 'local':
                self.start_odas_process()
                if not self.running:
                    return

            if self.forward_to_gui:
                self.connect_to_gui()

            self.tracked_server = self.start_server(self.tracked_port)
            self.potential_server = self.start_server(self.potential_port)

            self.doa_animation.start()

            print(f"ODAS DoA/SSL Processor started: mode={self.mode}, tracked={self.tracked_port}, "
                  f"potential={self.potential_port}, GUI forwarding={'on' if self.forward_to_gui else 'off'}, "
                  f"debug={'on' if self.debug_mode else 'off'}")

            status_thread = threading.Thread(target=self._status_check_thread)
            status_thread.daemon = True
            status_thread.start()
            self.threads.append(status_thread)

            tracked_thread = threading.Thread(
                target=self.accept_and_handle,
                args=(self.tracked_server, "tracked")
            )
            potential_thread = threading.Thread(
                target=self.accept_and_handle,
                args=(self.potential_server, "potential")
            )
            
            tracked_thread.start()
            potential_thread.start()
            
            self.threads.extend([tracked_thread, potential_thread])
            
            for thread in self.threads:
                thread.join()
                
        except Exception as e:
            self.log(f"Start error: {e}")
            self.running = False

    def accept_and_handle(self, server_socket: socket.socket, client_type: str) -> None:
        """Accept connections and handle clients in a loop."""
        while self.running:
            try:
                client_socket = self.accept_connection(server_socket, client_type)
                if client_socket:
                    self.handle_client(client_socket, client_type)
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    self.log(f"Accept/handle error: {str(e)}")
                time.sleep(1)

    def close(self) -> None:
        """Close the ODAS server and clean up resources."""
        self.running = False
        
        if hasattr(self, 'doa_animation'):
            self.doa_animation.stop_animation()
        
        for socket_obj in [self.tracked_server, self.potential_server,
                         self.tracked_client, self.potential_client,
                         self.gui_tracked_socket, self.gui_potential_socket]:
            if socket_obj:
                try:
                    socket_obj.close()
                except:
                    pass
        
        for log_file in self.log_files:
            try:
                log_file.close()
            except:
                pass
        
        if self.odas_process:
            try:
                self.odas_process.terminate()
                self.odas_process.wait(timeout=5)
            except:
                self.odas_process.kill()
        
        # Clear lights using the lights handler
        self.lights_handler.off()

def main() -> None:
    """Main entry point for the ODAS DoA/SSL processor."""
    parser = argparse.ArgumentParser(description='ODAS DoA/SSL Processor for sound source tracking')
    parser.add_argument('--mode', choices=['local', 'remote'], default='local',
                      help='Operation mode: local (127.0.0.1) or remote (default: local)')
    parser.add_argument('--host', default='192.168.0.171',
                      help='Host IP address for remote mode (default: 192.168.0.171)')
    parser.add_argument('--tracked-port', type=int, default=9000,
                      help='Port for tracked sources (default: 9000)')
    parser.add_argument('--potential-port', type=int, default=9001,
                      help='Port for potential sources (default: 9001)')
    parser.add_argument('--forward-to-gui', action='store_true',
                      help='Forward data to GUI station (default: False)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode with real-time source tracking display (default: False)')
    
    args = parser.parse_args()
    
    # Create a temporary lights handler for standalone mode
    from lights import LightsInteractionHandler
    lights_handler = LightsInteractionHandler({})  # Empty leg_to_led mapping for standalone mode
    
    server = ODASDoASSLProcessor(
        lights_handler=lights_handler,
        mode=args.mode,
        host=args.host,
        tracked_port=args.tracked_port,
        potential_port=args.potential_port,
        forward_to_gui=args.forward_to_gui,
        debug_mode=args.debug
    )

    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()

if __name__ == "__main__":
    main()