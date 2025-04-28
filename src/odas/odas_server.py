#!/usr/bin/env python3

"""
ODAS (Open embeddeD Audition System) Server Implementation

This module implements a server that receives and processes sound source data from ODAS.
It handles two separate data streams:
1. Tracked sources: Currently active and tracked sound sources
2. Potential sources: New or untracked sound sources being detected

The server creates and manages log files for both types of sources, providing real-time
monitoring and status updates.

Example:
    >>> server = ODASServer()
    >>> server.start()
"""

import socket
import struct
import json
import time
import threading
from datetime import datetime
import os
import signal
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, TextIO, Any, Dict, Tuple
import argparse

logger = logging.getLogger("odas")
# logging.basicConfig(level=logging.INFO)

class ODASServer:
    """
    ODAS Server implementation that handles sound source tracking and logging.

    The server manages two separate TCP connections for tracked and potential sources,
    processes the incoming data, and maintains log files for both types of sources.

    Attributes:
        host (str): IP address to bind the server to
        tracked_port (int): Port for tracked sources connection
        potential_port (int): Port for potential sources connection
        running (bool): Server running state flag
        log_files (list): List of open log file objects
        base_logs_dir (str): Path to the base logs directory
        mode (str): Operation mode - 'local' or 'remote'
        odas_process (subprocess.Popen): ODAS process handle when running in local mode
    """

    def __init__(self, mode: str = 'local', host: str = '192.168.0.171', tracked_port: int = 9000, potential_port: int = 9001) -> None:
        """
        Initialize the ODAS server with configuration parameters.

        Args:
            mode (str): Operation mode - 'local' or 'remote' (default: 'local')
            host (str): IP address to bind the server to (default: '192.168.0.171')
            tracked_port (int): Port for tracked sources (default: 9000)
            potential_port (int): Port for potential sources (default: 9001)
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

        # Create base logs directory in hexapod root
        workspace_root: Path = Path(__file__).parent.parent.parent
        self.base_logs_dir: Path = workspace_root / "logs" / "odas"
        try:
            self.base_logs_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created log directory: {self.base_logs_dir}")
        except Exception as e:
            print(f"Error creating log directory {self.base_logs_dir}: {str(e)}")
            # Fallback to current directory
            self.base_logs_dir = Path(__file__).parent

        # Create log files with fixed names
        self.tracked_log: TextIO = self._open_log_file(self.base_logs_dir / "tracked.log")
        self.potential_log: TextIO = self._open_log_file(self.base_logs_dir / "potential.log")

        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def _open_log_file(self, path: Path) -> TextIO:
        """
        Open a log file and add it to the list of managed log files.

        Args:
            path (Path): Path to the log file to open

        Returns:
            TextIO: Opened file object or a dummy file object if opening fails
        """
        try:
            log_file: TextIO = open(path, "w")
            self.log_files.append(log_file)
            print(f"Created log file: {path}")
            return log_file
        except Exception as e:
            print(f"Error creating log file {path}: {str(e)}")
            # Create a dummy file object that does nothing
            class DummyFile:
                def write(self, *args: Any, **kwargs: Any) -> None: pass
                def flush(self, *args: Any, **kwargs: Any) -> None: pass
                def close(self, *args: Any, **kwargs: Any) -> None: pass
            return DummyFile()

    def signal_handler(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signals (SIGINT, SIGTERM).

        Args:
            signum (int): Signal number
            frame: Current stack frame
        """
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False

    def log(self, message: str, log_file: Optional[TextIO] = None, print_to_console: bool = False) -> None:
        """
        Log a message to console and optionally to a specific log file.

        Args:
            message (str): Message to log
            log_file (TextIO, optional): Specific log file to write to
            print_to_console (bool): Whether to print to console (default: False)
        """
        if not self.running:
            return  # Don't log during shutdown
        
        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message: str = f"[{timestamp}] {message}\n"
        
        if print_to_console:
            print(log_message, end='')
        
        try:
            if log_file:
                log_file.write(log_message)
                log_file.flush()
        except:
            pass  # Ignore write errors during shutdown

    def start_server(self, port: int) -> socket.socket:
        """
        Start a TCP server on the specified port.

        Args:
            port (int): Port number to bind the server to

        Returns:
            socket.socket: Server socket object
        """
        server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, port))
        server_socket.listen(1)
        self.log(f"Server listening on {self.host}:{port}", print_to_console=True)
        return server_socket

    def handle_client(self, client_socket: socket.socket, client_type: str) -> None:
        """
        Handle data from a connected client.

        Processes incoming data from either tracked or potential sources,
        parses JSON data, and logs it appropriately.

        Args:
            client_socket (socket.socket): Client socket connection
            client_type (str): Type of client ("tracked" or "potential")
        """
        log_file: TextIO = self.tracked_log if client_type == "tracked" else self.potential_log
        active_sources_count: int = 0
        last_status_time: float = time.time()
        
        while self.running:
            try:
                # Set a timeout for recv operations
                client_socket.settimeout(1.0)
                
                # Read the size of the message (4 bytes)
                size_bytes: bytes = client_socket.recv(4)
                if not size_bytes:
                    self.log(f"{client_type} client disconnected", log_file, print_to_console=True)
                    break

                # Convert size to integer
                size: int = struct.unpack('I', size_bytes)[0]

                # Read the message
                data: bytes = client_socket.recv(size)
                if not data:
                    break

                try:
                    # Clean the JSON data
                    json_str: str = data.decode('utf-8').strip()
                    
                    # Split the string into individual JSON objects
                    json_objects: List[str] = []
                    start: int = 0
                    while True:
                        # Find the next '{' and '}' pair
                        start_brace: int = json_str.find('{', start)
                        if start_brace == -1:
                            break
                        
                        # Find matching closing brace
                        brace_count: int = 1
                        end_brace: int = start_brace + 1
                        while brace_count > 0 and end_brace < len(json_str):
                            if json_str[end_brace] == '{':
                                brace_count += 1
                            elif json_str[end_brace] == '}':
                                brace_count -= 1
                            end_brace += 1
                        
                        if brace_count == 0:
                            # Extract the JSON object
                            json_obj: str = json_str[start_brace:end_brace]
                            json_objects.append(json_obj)
                            start = end_brace
                        else:
                            break
                    
                    # Process each JSON object
                    current_active_sources: int = 0
                    for json_obj in json_objects:
                        try:
                            json_data: Dict[str, Any] = json.loads(json_obj)
                            
                            if client_type == "tracked":
                                # For tracked sources, only log if it's an active source (non-zero ID)
                                if 'id' in json_data and json_data['id'] != 0:
                                    current_active_sources += 1
                                    self.log(f"\nActive tracked source:", log_file)
                                    self.log(json.dumps(json_data, indent=2), log_file)
                            else:
                                # For potential sources, log all entries as they represent new detections
                                self.log(f"\nPotential source detection:", log_file)
                                self.log(json.dumps(json_data, indent=2), log_file)
                            
                        except json.JSONDecodeError as e:
                            self.log(f"\nJSON Parse Error in object: {str(e)}", log_file)
                            self.log(f"Problematic object: {json_obj}", log_file)
                    
                    # Update active sources count and log status periodically
                    if client_type == "tracked" and current_active_sources != active_sources_count:
                        active_sources_count = current_active_sources
                        self.log(f"\nCurrently tracking {active_sources_count} active sources", log_file, print_to_console=True)
                    
                    # Log status every 15 seconds
                    current_time: float = time.time()
                    if current_time - last_status_time >= 15:
                        last_status_time = current_time
                        if client_type == "tracked":
                            if active_sources_count == 0:
                                self.log(f"\nNo active sources detected in the last 15 seconds", log_file, print_to_console=True)
                            else:
                                self.log(f"\nMonitoring for new potential sources", log_file, print_to_console=True)
                    
                    if not json_objects:
                        self.log(f"\nNo valid JSON objects found", log_file)
                        self.log(f"Raw data: {json_str}", log_file)
                    
                except Exception as e:
                    self.log(f"\nError processing data: {str(e)}", log_file)
                    self.log(f"Raw data: {data.decode('utf-8', errors='replace')}", log_file)
                    
            except socket.timeout:
                # Timeout is expected, just continue the loop
                continue
            except (ConnectionResetError, BrokenPipeError):
                self.log(f"{client_type} connection reset", log_file, print_to_console=True)
                break
            except Exception as e:
                if self.running:  # Only log errors if we're still running
                    self.log(f"Error in {client_type} handler: {str(e)}", log_file, print_to_console=True)
                break

    def accept_connection(self, server_socket: socket.socket, client_type: str) -> Optional[socket.socket]:
        """
        Accept a connection from a client.

        Args:
            server_socket (socket.socket): Server socket to accept from
            client_type (str): Type of client ("tracked" or "potential")

        Returns:
            Optional[socket.socket]: Client socket or None if accept fails
        """
        try:
            server_socket.settimeout(1.0)  # Set timeout for accept
            client_socket: socket.socket
            address: Tuple[str, int]
            client_socket, address = server_socket.accept()
            log_file: TextIO = self.tracked_log if client_type == "tracked" else self.potential_log
            self.log(f"{client_type} connected from {address}", log_file, print_to_console=True)
            return client_socket
        except socket.timeout:
            return None
        except Exception as e:
            if self.running:  # Only log errors if we're still running
                self.log(f"Error accepting {client_type} connection: {str(e)}", print_to_console=True)
            return None

    def start_odas_process(self) -> None:
        """
        Start the ODAS process in local mode.
        """
        if self.mode != 'local':
            return

        try:
            # Get the path to the config file
            config_path = Path(__file__).parent / "config" / "local_odas.cfg"
            if not config_path.exists():
                raise FileNotFoundError(f"ODAS config file not found at {config_path}")

            # Start the ODAS process
            self.odas_process = subprocess.Popen(
                ["odaslive", "-c", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"Started ODAS process with PID {self.odas_process.pid}")
            
            # Start a thread to monitor the ODAS process output
            threading.Thread(target=self._monitor_odas_output, daemon=True).start()
            
        except Exception as e:
            print(f"Error starting ODAS process: {str(e)}")
            self.running = False

    def _monitor_odas_output(self) -> None:
        """
        Monitor the ODAS process output and log it.
        """
        if not self.odas_process:
            return

        try:
            while self.running and self.odas_process.poll() is None:
                # Read stdout and stderr
                stdout = self.odas_process.stdout.readline() if self.odas_process.stdout else None
                stderr = self.odas_process.stderr.readline() if self.odas_process.stderr else None

                if stdout:
                    print(f"ODAS: {stdout.strip()}")
                if stderr:
                    print(f"ODAS Error: {stderr.strip()}")

        except Exception as e:
            print(f"Error monitoring ODAS output: {str(e)}")

    def start(self) -> None:
        """
        Start the ODAS server.

        Initializes both tracked and potential source servers, starts connection
        handling threads, and manages the server lifecycle.
        """
        try:
            # Start ODAS process if in local mode
            if self.mode == 'local':
                self.start_odas_process()
                if not self.running:
                    return

            # Start both servers first
            self.tracked_server = self.start_server(self.tracked_port)
            self.potential_server = self.start_server(self.potential_port)

            # Log startup information
            self.log("ODAS Server started", print_to_console=True)
            self.log("Tracked sources: Currently active and tracked sound sources", print_to_console=True)
            self.log("Note: Only active tracked sources (non-zero IDs) will be logged in tracked.log", print_to_console=True)
            self.log("Potential sources: New or untracked sound sources being detected", print_to_console=True)
            self.log("All potential sources will be logged in potential.log", print_to_console=True)
            self.log("Check microphone configuration and tracking parameters if no sources are detected", print_to_console=True)

            # Accept connections in separate threads
            tracked_thread: threading.Thread = threading.Thread(
                target=self.accept_and_handle,
                args=(self.tracked_server, "tracked")
            )
            potential_thread: threading.Thread = threading.Thread(
                target=self.accept_and_handle,
                args=(self.potential_server, "potential")
            )

            # Store threads for later cleanup
            self.threads = [tracked_thread, potential_thread]

            # Start threads
            for thread in self.threads:
                thread.start()

            # Wait for both threads to complete
            for thread in self.threads:
                thread.join()

        except Exception as e:
            print(f"Error in server: {str(e)}")
            self.running = False

    def accept_and_handle(self, server_socket: socket.socket, client_type: str) -> None:
        """
        Accept connections and handle clients in a loop.

        Args:
            server_socket (socket.socket): Server socket to accept from
            client_type (str): Type of client ("tracked" or "potential")
        """
        while self.running:
            try:
                client_socket: Optional[socket.socket] = self.accept_connection(server_socket, client_type)
                if client_socket:
                    self.handle_client(client_socket, client_type)
                time.sleep(0.1)  # Small delay to prevent CPU overload
            except Exception as e:
                if self.running:  # Only log errors if we're still running
                    self.log(f"Error in {client_type} acceptor: {str(e)}")
                time.sleep(1)  # Wait before retrying

    def close(self) -> None:
        """
        Close all connections and log files.

        Performs graceful shutdown by:
        1. Closing client connections
        2. Closing server sockets
        3. Waiting for threads to finish
        4. Closing log files
        5. Terminating ODAS process if running in local mode
        """
        print("\nShutting down server...")
        self.running = False

        # Terminate ODAS process if running
        if self.odas_process:
            try:
                self.odas_process.terminate()
                self.odas_process.wait(timeout=5)
            except:
                try:
                    self.odas_process.kill()
                except:
                    pass
            finally:
                self.odas_process = None

        # Close client sockets
        for client in [self.tracked_client, self.potential_client]:
            if client:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                    client.close()
                except:
                    pass

        # Close server sockets
        for server in [self.tracked_server, self.potential_server]:
            if server:
                try:
                    server.close()
                except:
                    pass

        # Wait for threads to finish
        for thread in self.threads:
            try:
                thread.join(timeout=1.0)
            except:
                pass
        
        # Close log files
        for log_file in self.log_files:
            try:
                log_file.close()
            except:
                pass

        print("Server shutdown complete")

def main() -> None:
    """
    Main entry point for the ODAS server.

    Creates and runs the server, handling keyboard interrupts for graceful shutdown.
    """
    parser = argparse.ArgumentParser(description='ODAS Server for sound source tracking')
    parser.add_argument('--mode', choices=['local', 'remote'], default='local',
                      help='Operation mode: local (127.0.0.1) or remote (default: local)')
    parser.add_argument('--host', default='192.168.0.171',
                      help='Host IP address for remote mode (default: 192.168.0.171)')
    parser.add_argument('--tracked-port', type=int, default=9000,
                      help='Port for tracked sources (default: 9000)')
    parser.add_argument('--potential-port', type=int, default=9001,
                      help='Port for potential sources (default: 9001)')
    
    args = parser.parse_args()
    
    # Create ODAS server with parsed arguments
    server: ODASServer = ODASServer(
        mode=args.mode,
        host=args.host,
        tracked_port=args.tracked_port,
        potential_port=args.potential_port
    )

    try:
        # Start the servers
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()

if __name__ == "__main__":
    main() 