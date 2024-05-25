"""
This server code implements a naming server for a distributed file system. It handles multiple types of requests from storage servers and clients, managing registration, heartbeats, and queries about the status of connected servers. The script is designed to run continuously, listening on a specified IP address and port provided via command-line arguments.

Features include:
- **Registration**: Storage servers can register themselves with their IP address and a unique port. This registration helps in tracking which servers are active and their last known state.
- **Heartbeat Monitoring**: Registered servers must send heartbeats periodically. This mechanism helps the naming server keep track of which servers are still active. If a server fails to send a heartbeat within a designated timeout, it's marked as down.
- **Query Handling**: Clients and servers can query the naming server to get a list of servers that are currently marked as 'alive'. This is useful for determining where to route client requests or data storage.
- **Updates on Server Files**: Servers inform the naming server about changes to their stored files, enabling the naming server to maintain an up-to-date index of file locations.

Each client and server connection is handled in its own thread, allowing the server to manage multiple simultaneous connections. The server uses JSON for communication, which simplifies data parsing and handling across different platforms.

Usage:
To start the server, you need to provide the host and port as command-line arguments. For example:
    python server.py 127.0.0.1 9999
This command starts the server listening on localhost at port 9999.
"""


import socket
import threading
import json
import time
import sys  # Needed to access command-line arguments

# Dynamically track storage servers
storage_servers = {}

def client_handler(conn, client_ip):
    """ Handle requests from connected clients. """
    global storage_servers
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            request = json.loads(data)

            if 'type' not in request:
                response = {'status': 'error', 'message': 'Missing type information'}
                conn.sendall(json.dumps(response).encode())
                continue

            # Check for 'port' in requests that require it
            if request['type'] in ['register', 'heartbeat'] and 'port' not in request:
                response = {'status': 'error', 'message': 'Missing necessary port information for register or heartbeat'}
                conn.sendall(json.dumps(response).encode())
                continue

            # Process requests based on their type
            if request['type'] == 'register':
                server_id = f"{client_ip}:{request['port']}"
                storage_servers[server_id] = {'status': 'alive', 'files': [], 'last_heartbeat': time.time()}
                response = {'status': 'registered'}
            elif request['type'] == 'heartbeat':
                server_id = f"{client_ip}:{request['port']}"
                if server_id in storage_servers:
                    storage_servers[server_id]['last_heartbeat'] = time.time()
                    storage_servers[server_id]['status'] = 'alive'
                response = {'status': 'heartbeat acknowledged'}
            elif request['type'] == 'query':
                response = handle_query()
            elif request['type'] == 'update':
                server_id = f"{client_ip}:{request['port']}"
                response = handle_heartbeat(request, server_id)

            conn.sendall(json.dumps(response).encode())
    except Exception as e:
        print(f"Exception in client_handler: {e}")
    finally:
        conn.close()

def handle_query():
    """ Retrieve list of servers that are alive. """
    alive_servers = [server for server, data in storage_servers.items() if data['status'] == 'alive']
    return {'servers': alive_servers}

def handle_heartbeat(request, server_id):
    """ Update heartbeat for a registered server. """
    if server_id in storage_servers:
        storage_servers[server_id]['last_heartbeat'] = time.time()
        storage_servers[server_id]['status'] = 'alive'
        return {'status': 'heartbeat acknowledged'}
    else:
        return {'status': 'error', 'message': 'Server not registered'}

def monitor_servers():
    """ Monitor and update the status of registered servers. """
    while True:
        current_time = time.time()
        for server, data in list(storage_servers.items()):
            if current_time - data['last_heartbeat'] > 50:  # Assume 50 seconds timeout
                data['status'] = 'down'
        time.sleep(5)

def start_server(host, port):
    """ Start the naming server listening on the given host and port. """
    server_thread = threading.Thread(target=monitor_servers)
    server_thread.start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Naming Server listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            thread = threading.Thread(target=client_handler, args=(conn, addr[0]))
            thread.start()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py [host] [port]")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    start_server(host, port)
