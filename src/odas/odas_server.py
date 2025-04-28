#!/usr/bin/env python3

import socket
import struct
import json
import time
import threading

class ODASServer:
    def __init__(self, host='192.168.0.171', tracked_port=9000, potential_port=9001):
        self.host = host
        self.tracked_port = tracked_port
        self.potential_port = potential_port
        self.tracked_server = None
        self.potential_server = None
        self.tracked_client = None
        self.potential_client = None

    def start_server(self, port):
        """Start a server on the specified port"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, port))
        server_socket.listen(1)
        print(f"Server listening on {self.host}:{port}")
        return server_socket

    def handle_client(self, client_socket, client_type):
        """Handle data from a connected client"""
        while True:
            try:
                # Read the size of the message (4 bytes)
                size_bytes = client_socket.recv(4)
                if not size_bytes:
                    print(f"{client_type} client disconnected")
                    break

                # Convert size to integer
                size = struct.unpack('I', size_bytes)[0]

                # Read the message
                data = client_socket.recv(size)
                if not data:
                    break

                # Parse JSON data
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    print(f"\nReceived {client_type} data:")
                    print(json.dumps(json_data, indent=2))
                except json.JSONDecodeError:
                    print(f"Error decoding {client_type} JSON data")
            except ConnectionResetError:
                print(f"{client_type} connection reset")
                break

    def start(self):
        """Start both servers and handle connections"""
        # Start tracked sources server
        self.tracked_server = self.start_server(self.tracked_port)
        print("Waiting for tracked sources connection...")
        self.tracked_client, tracked_addr = self.tracked_server.accept()
        print(f"Tracked sources connected from {tracked_addr}")

        # Start potential sources server
        self.potential_server = self.start_server(self.potential_port)
        print("Waiting for potential sources connection...")
        self.potential_client, potential_addr = self.potential_server.accept()
        print(f"Potential sources connected from {potential_addr}")

        # Start threads to handle both connections
        tracked_thread = threading.Thread(
            target=self.handle_client,
            args=(self.tracked_client, "tracked")
        )
        potential_thread = threading.Thread(
            target=self.handle_client,
            args=(self.potential_client, "potential")
        )

        tracked_thread.start()
        potential_thread.start()

        # Wait for both threads to complete
        tracked_thread.join()
        potential_thread.join()

    def close(self):
        """Close all connections"""
        if self.tracked_client:
            self.tracked_client.close()
        if self.potential_client:
            self.potential_client.close()
        if self.tracked_server:
            self.tracked_server.close()
        if self.potential_server:
            self.potential_server.close()

def main():
    # Create ODAS server
    server = ODASServer()

    try:
        # Start the servers
        server.start()
    except KeyboardInterrupt:
        print("\nStopping ODAS server...")
    finally:
        server.close()

if __name__ == "__main__":
    main() 