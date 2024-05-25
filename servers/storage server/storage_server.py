"""
This script implements a storage server for a distributed file system. It is designed to handle file operations such as PUT, GET, and LIST, 
manage registration with a naming server, and send periodic heartbeats to indicate its active status. The server listens for client requests
on a specified IP and port, handling each connection in a separate thread.

Features:
- Handles file operations including writing files (PUT), reading files (GET), and listing all files in the directory (LIST).
- Registers itself with a central naming server and periodically sends heartbeats to maintain its 'alive' status.
- Uses a base directory to store all files, isolating stored data from the system to improve security and organization.

Usage:
To run the server, provide the local host IP, local port, naming server host IP, naming server port, and path to the storage directory
as command-line arguments. For example:
    python storage_server.py 127.0.0.1 10000 127.0.0.1 9999 
"""


import socket
import threading
import time
import json
import os
import sys

def handle_client(conn, base_directory):
    while True:
        try:
            data = conn.recv(1024).decode()
        except:
            pass
        
        if not data:
            break
        command, filepath, content,username = data.split('|', 3)
        
    

        try:
            if command == 'PUT':
                if not os.path.exists(f'content/{username}'):
                    os.makedirs(f'content/{username}')
                    
                with open(f'content/{username}/{filepath}', 'w') as f:
                    f.write(content)
                    f.close()
                response = 'PUT_COMPLETE'
            elif command == 'GET':
                
                if not os.path.exists(f'content/{username}'):
                    os.makedirs(f'content/{username}')
         
                with open(f'content/{username}/{filepath}', 'r') as f:
                        response = f.read()
                        
                        if response == "":
                            response = "FILE IS_EMPTY"
                        f.close()
            elif command == 'LIST':
                
                if not os.path.exists(f'content/{username}'):
                    os.makedirs(f'content/{username}')
                   
                
                files = os.listdir(f'content/{username}')
                response = json.dumps(files)


                
            else:
                response = 'FILE_NOT_FOUND'
        except IOError as e:
            response = f"ERROR: {e.strerror}"
        try:
            
            conn.sendall(response.encode())
        except:
            pass
    conn.close()

def register_with_naming_server(naming_server_host, naming_server_port, local_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((naming_server_host, naming_server_port))
            register_message = json.dumps({
                'type': 'register',
                'port': local_port  # Including local port information
            })
            s.sendall(register_message.encode())
            response = json.loads(s.recv(1024).decode())
            print("Registration response:", response)
    except Exception as e:
        print(f"Failed to register with naming server: {e}")

def send_heartbeat(naming_server_host, naming_server_port, local_port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((naming_server_host, naming_server_port))
                heartbeat_message = json.dumps({
                    'type': 'heartbeat',
                    'port': local_port  # Including local port information
                })
                s.sendall(heartbeat_message.encode())
                response = s.recv(1024).decode()
                print("Heartbeat response:", response)
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
        time.sleep(5)  # send a heartbeat every 5 seconds

def start_server(local_host, local_port, naming_server_host, naming_server_port, storage_directory):
    if not os.path.exists(storage_directory):
        os.makedirs(storage_directory)

    register_with_naming_server(naming_server_host, naming_server_port, local_port)
    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(naming_server_host, naming_server_port, local_port))
    heartbeat_thread.start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((local_host, local_port))
        s.listen()
        print(f"Storage Server listening on {local_host}:{local_port}")
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=handle_client, args=(conn, storage_directory))
            thread.start()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python storage_server.py [local_host] [local_port] [naming_server_host] [naming_server_port]")
        sys.exit(1)

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    naming_server_host = sys.argv[3]
    naming_server_port = int(sys.argv[4])
    storage_directory = "/content"
    start_server(local_host, local_port, naming_server_host, naming_server_port, storage_directory)
