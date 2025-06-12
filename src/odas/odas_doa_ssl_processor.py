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
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, TextIO, Any, Dict
import argparse
import sys
import math

if __name__ == "__main__":
    current_file = Path(__file__)
    src_dir = str(current_file.parent.parent)
    if src_dir not in sys.path:
        sys.path.append(src_dir)

from lights import LightsInteractionHandler

logger = logging.getLogger("odas_logger")

class ODASDoASSLProcessor:
    """
    ODAS DoA (Direction of Arrival) and SSL (Sound Source Localization) processor implementation.
    Handles sound source tracking, processing, and visualization.
    """

    class DataManager:
        """
        Manages data-related operations including directory management, file handling, and logging.
        """
        def __init__(
            self,
            processor: 'ODASDoASSLProcessor',
            workspace_root: Path = Path(__file__).parent.parent.parent,
            base_logs_dir: Path = Path(__file__).parent.parent.parent / "logs" / "odas" / "ssl",
            odas_data_dir: Path = Path(__file__).parent.parent.parent / "data" / "audio" / "odas"
        ) -> None:
            """Initialize the data manager."""
            self.processor = processor
            self.workspace_root: Path = workspace_root
            self.base_logs_dir: Path = base_logs_dir
            self.odas_data_dir: Path = odas_data_dir
            self.log_files: List[TextIO] = []
            self.tracked_log: Optional[TextIO] = None
            self.potential_log: Optional[TextIO] = None

        def setup(self) -> None:
            """Setup all required directories and files."""
            try:
                # Setup logging directories and files
                self.base_logs_dir.mkdir(parents=True, exist_ok=True)
                self.tracked_log = self._open_log_file(self.base_logs_dir / "tracked.log")
                self.potential_log = self._open_log_file(self.base_logs_dir / "potential.log")

                # Setup ODAS data directories
                self.odas_data_dir.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                logger.error(f"Error setting up directories: {str(e)}")
                # Fallback to current directory for logs if setup fails
                self.base_logs_dir = Path(__file__).parent
                self.tracked_log = self._open_log_file(self.base_logs_dir / "tracked.log")
                self.potential_log = self._open_log_file(self.base_logs_dir / "potential.log")

        def _open_log_file(self, path: Path) -> TextIO:
            """Open a log file and add it to the list of managed log files."""
            try:
                log_file: TextIO = open(path, "w")
                self.log_files.append(log_file)
                return log_file
            except Exception as e:
                logger.error(f"Error creating log file: {str(e)}")
                class DummyFile:
                    def write(self, *args: Any, **kwargs: Any) -> None: pass
                    def flush(self, *args: Any, **kwargs: Any) -> None: pass
                    def close(self, *args: Any, **kwargs: Any) -> None: pass
                return DummyFile()

        def log(self, message: str, log_file: Optional[TextIO] = None, print_to_console: bool = False) -> None:
            """Log a message to console and optionally to a specific log file."""
            if not self.processor.running:
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

        def close(self) -> None:
            """Close all managed log files."""
            for log_file in self.log_files:
                try:
                    log_file.close()
                except:
                    pass
            self.log_files.clear()

    class GUIManager:
        """
        Manages GUI-related operations including connection handling and data forwarding.
        """
        def __init__(
            self,
            processor: 'ODASDoASSLProcessor',
            gui_host: str = "192.168.0.102",
            gui_tracked_sources_port: int = 9000,
            gui_potential_sources_port: int = 9001,
            forward_to_gui: bool = False,
            gui_tracked_sources_socket: Optional[socket.socket] = None,
            gui_potential_sources_socket: Optional[socket.socket] = None
        ) -> None:
            """Initialize the GUI manager."""
            self.processor = processor
            self.gui_host: str = gui_host
            self.gui_tracked_sources_port: int = gui_tracked_sources_port
            self.gui_potential_sources_port: int = gui_potential_sources_port
            self.gui_tracked_sources_socket: Optional[socket.socket] = gui_tracked_sources_socket
            self.gui_potential_sources_socket: Optional[socket.socket] = gui_potential_sources_socket
            self.forward_to_gui: bool = forward_to_gui

        def connect(self) -> None:
            """Connect to the remote GUI station."""
            try:
                self.gui_tracked_sources_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.gui_tracked_sources_socket.connect((self.gui_host, self.gui_tracked_sources_port))
                self.gui_potential_sources_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.gui_potential_sources_socket.connect((self.gui_host, self.gui_potential_sources_port))
                print(f"Connected to GUI at {self.gui_host}")
            except Exception as e:
                logger.error(f"GUI connection error: {str(e)}")
                print("Disabling GUI forwarding...")
                self.forward_to_gui = False
                self._close_sockets()

        def _close_sockets(self) -> None:
            """Close GUI sockets."""
            if self.gui_tracked_sources_socket:
                self.gui_tracked_sources_socket.close()
                self.gui_tracked_sources_socket = None
            if self.gui_potential_sources_socket:
                self.gui_potential_sources_socket.close()
                self.gui_potential_sources_socket = None

        def handle_disconnection(self) -> None:
            """Handle GUI disconnection by attempting to reconnect or disabling forwarding."""
            try:
                self._close_sockets()
                self.connect()
            except Exception as e:
                logger.error(f"Failed to reconnect to GUI: {str(e)}")
                print("Disabling GUI forwarding...")
                self.forward_to_gui = False

        def forward_data(self, data: bytes, client_type: str) -> None:
            """Forward data to the GUI station."""
            try:
                if client_type == "tracked" and self.gui_tracked_sources_socket:
                    self.gui_tracked_sources_socket.send(data)
                elif client_type == "potential" and self.gui_potential_sources_socket:
                    self.gui_potential_sources_socket.send(data)
            except (BrokenPipeError, ConnectionResetError):
                logger.error("GUI connection lost. Attempting to reconnect...")
                self.handle_disconnection()
            except Exception as e:
                logger.error(f"GUI forward error: {str(e)}")

        def close(self) -> None:
            """Close all GUI connections."""
            self._close_sockets()

    def __init__(
        self,
        lights_handler: LightsInteractionHandler,
        tracked_sources_port: int = 9000,
        potential_sources_port: int = 9001,
        debug_mode: bool = False,
        gui_config: Optional[Dict[str, Any]] = None,
        data_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the ODAS server with configuration parameters.

        Args:
            lights_handler (LightsInteractionHandler): The lights handler to use for visualization.
            tracked_sources_port (int): Port for data from incoming odas tracked sound sources.
            potential_sources_port (int): Port for data from incoming odas potential sound sources.
            debug_mode (bool): Whether to enable debug mode.
            gui_config (Optional[Dict[str, Any]]): Configuration for GUI manager.
            data_config (Optional[Dict[str, Any]]): Configuration for data manager.
        """
        self.host: str = '127.0.0.1'
        self.tracked_sources_port: int = tracked_sources_port
        self.potential_sources_port: int = potential_sources_port
        self.tracked_sources_server: Optional[socket.socket] = None
        self.potential_sources_server: Optional[socket.socket] = None
        self.tracked_sources_client: Optional[socket.socket] = None
        self.potential_sources_client: Optional[socket.socket] = None
        self.running: bool = True
        self.threads: List[threading.Thread] = []
        self.odas_process: Optional[subprocess.Popen] = None

        # Initialize managers
        self.data_manager = self.DataManager(self, **(data_config or {}))
        self.gui_manager = self.GUIManager(self, **(gui_config or {}))
        self.data_manager.setup()

        # Initialize LED visualization using the provided lights handler
        self.lights_handler = lights_handler
        self.tracked_sources: Dict[int, Dict] = {}
        self.potential_sources: Dict[int, Dict] = {}
        self.sources_lock: threading.Lock = threading.Lock()

        # Debug mode and display control
        self.debug_mode: bool = debug_mode
        self.last_num_lines: int = 0  # Track number of lines printed last update
        self.initial_connection_made: bool = False

    def handle_odas_data(self, client_socket: socket.socket, client_type: str) -> None:
        """Handle data from a connected client."""
        log_file: TextIO = self.data_manager.tracked_log if client_type == "tracked" else self.data_manager.potential_log
        
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

                if self.gui_manager.forward_to_gui:
                    self.gui_manager.forward_data(size_bytes + data, client_type)

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
                                    self.data_manager.log(f"Tracked source detected:", log_file)
                                    self.data_manager.log(json.dumps(source_data, indent=2), log_file)
                            else:
                                source_id = len(self.potential_sources)
                                with self.sources_lock:
                                    self.potential_sources[source_id] = source_data
                                self.data_manager.log(f"Potential source detected:", log_file)
                                self.data_manager.log(json.dumps(source_data, indent=2), log_file)
                            
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
                        
                        with self.sources_lock:
                            self.tracked_sources = active_sources
                        
                        if self.debug_mode:
                            self._print_debug_info(active_sources)
                    
                    with self.sources_lock:
                        tracked_sources_copy = dict(self.tracked_sources)
                    
                    # Update the animation through the lights handler
                    if hasattr(self.lights_handler.animation, 'update_sources'):
                        self.lights_handler.animation.update_sources(tracked_sources_copy)
                    
                except Exception as e:
                    continue
                    
            except socket.timeout:
                continue
            except (ConnectionResetError, BrokenPipeError):
                break
            except Exception as e:
                if self.running:
                    logger.error(f"ODAS data handler error: {str(e)}")
                break

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

    def accept_and_handle_data(self, server_socket: socket.socket, client_type: str) -> None:
        """Accept connections and handle ODAS data in a loop."""
        def _accept_connection(server_socket: socket.socket, client_type: str) -> Optional[socket.socket]:
            """Accept a connection from a client."""
            try:
                server_socket.settimeout(1.0)
                client_socket, address = server_socket.accept()
                return client_socket
            except socket.timeout:
                return None
            except Exception as e:
                if self.running:
                    logger.error(f"Accept error: {str(e)}")
                return None

        while self.running:
            try:
                client_socket = _accept_connection(server_socket, client_type)
                if client_socket:
                    self.handle_odas_data(client_socket, client_type)
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    logger.error(f"Accept/handle error: {str(e)}")
                time.sleep(1)

    def start_odas_process(self) -> None:
        """Start the ODAS process."""
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
            logger.error(f"ODAS start error: {str(e)}")
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
                    logger.error(f"ODAS Error: {stderr.strip()}")

        except Exception as e:
            logger.error(f"ODAS monitor error: {str(e)}")

    def _close_odas_process(self) -> None:
        """Close the ODAS process with graceful termination and fallback to force kill."""
        if not self.odas_process:
            return

        try:
            # First try graceful termination
            self.odas_process.terminate()
            try:
                self.odas_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If process doesn't terminate, force kill
                logger.warning("ODAS process did not terminate gracefully, forcing kill")
                self.odas_process.kill()
                self.odas_process.wait()
        except Exception as e:
            logger.error(f"Error terminating ODAS process: {e}")
            try:
                self.odas_process.kill()
            except:
                logger.error("Error killing ODAS process")
        finally:
            self.odas_process = None

    def start(self) -> None:
        """Start the ODAS DoA/SSL processor."""
        try:
            # Show loading animation while initializing
            self.lights_handler.odas_loading()

            self.start_odas_process()
            if not self.running:
                return

            if self.gui_manager.forward_to_gui:
                self.gui_manager.connect()

            self.tracked_sources_server = self.start_server(self.tracked_sources_port)
            self.potential_sources_server = self.start_server(self.potential_sources_port)

            # Wait for 2.2 seconds to complete one full loading animation cycle - let servers initialize
            time.sleep(2.2)

            # Switch to direction of arrival animation once everything is initialized
            self.lights_handler.direction_of_arrival()

            print(f"ODAS DoA/SSL Processor started: tracked={self.tracked_sources_port}, "
                  f"potential={self.potential_sources_port}, GUI forwarding={'on' if self.gui_manager.forward_to_gui else 'off'}, "
                  f"debug={'on' if self.debug_mode else 'off'}")

            tracked_thread = threading.Thread(
                target=self.accept_and_handle_data,
                args=(self.tracked_sources_server, "tracked")
            )
            potential_thread = threading.Thread(
                target=self.accept_and_handle_data,
                args=(self.potential_sources_server, "potential")
            )
            
            tracked_thread.start()
            potential_thread.start()
            
            self.threads.extend([tracked_thread, potential_thread])
            
            for thread in self.threads:
                thread.join()
                
        except Exception as e:
            logger.error(f"Start error: {e}")
            self.running = False

    def close(self) -> None:
        """Close the ODAS server and clean up resources."""
        self.running = False
        
        # Stop the animation through the lights handler
        self.lights_handler.off()
        
        for socket_obj in [self.tracked_sources_server, self.potential_sources_server,
                         self.tracked_sources_client, self.potential_sources_client]:
            if socket_obj:
                try:
                    socket_obj.close()
                except:
                    pass
        
        # Close all log files through the data manager
        self.data_manager.close()
        
        # Close GUI connections
        self.gui_manager.close()
        
        # Close ODAS process
        self._close_odas_process()

def main() -> None:
    """Main entry point for the ODAS DoA/SSL processor."""
    parser = argparse.ArgumentParser(description='ODAS DoA/SSL Processor for sound source tracking')
    parser.add_argument('--tracked-sources-port', type=int, default=9000,
                      help='Port for tracked sound sources (default: 9000)')
    parser.add_argument('--potential-sources-port', type=int, default=9001,
                      help='Port for potential sound sources (default: 9001)')
    parser.add_argument('--forward-to-gui', action='store_true',
                      help='Forward data to GUI station (default: False)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode with real-time source tracking display (default: False)')
    parser.add_argument('--gui-host', type=str, default="192.168.0.102",
                      help='Host address for GUI connection (default: 192.168.0.102)')
    parser.add_argument('--gui-tracked-sources-port', type=int, default=9000,
                      help='Port for tracked sound sources in GUI (default: 9000)')
    parser.add_argument('--gui-potential-sources-port', type=int, default=9001,
                      help='Port for potential sound sources in GUI (default: 9001)')
    parser.add_argument('--workspace-root', type=str,
                      help='Root directory for workspace (default: script directory)')
    parser.add_argument('--base-logs-dir', type=str,
                      help='Directory for log files (default: workspace_root/logs/odas/ssl)')
    parser.add_argument('--odas-data-dir', type=str,
                      help='Directory for ODAS data files (default: workspace_root/data/audio/odas)')
    
    args = parser.parse_args()
    
    # Create a temporary lights handler for standalone mode
    from lights import LightsInteractionHandler
    lights_handler = LightsInteractionHandler({})  # Empty leg_to_led mapping for standalone mode
    
    # Prepare configurations
    gui_config = {
        'gui_host': args.gui_host,
        'gui_tracked_sources_port': args.gui_tracked_sources_port,
        'gui_potential_sources_port': args.gui_potential_sources_port,
        'forward_to_gui': args.forward_to_gui
    }
    
    data_config = {}
    if args.workspace_root:
        data_config['workspace_root'] = Path(args.workspace_root)
    if args.base_logs_dir:
        data_config['base_logs_dir'] = Path(args.base_logs_dir)
    if args.odas_data_dir:
        data_config['odas_data_dir'] = Path(args.odas_data_dir)
    
    server = ODASDoASSLProcessor(
        lights_handler=lights_handler,
        tracked_sources_port=args.tracked_sources_port,
        potential_sources_port=args.potential_sources_port,
        debug_mode=args.debug,
        gui_config=gui_config,
        data_config=data_config
    )

    try:
        server.start()
    except KeyboardInterrupt:
        logger.critical("KeyboardInterrupt detected, initiating shutdown")
        sys.stdout.write('\b' * 2)
        logger.critical('Stopping ODAS DoA/SSL processor and cleaning up due to keyboard interrupt...')
    finally:
        server.close()

if __name__ == "__main__":
    main()