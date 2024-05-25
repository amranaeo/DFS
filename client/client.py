import socket
import json
import sys
import mysql.connector
from mysql.connector import Error
import hashlib
import getpass
from colorama import init, Fore, Style

init(autoreset=True)

def contact_naming_server_for_info(filename, naming_server_host, naming_server_port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((naming_server_host, naming_server_port))
            request = json.dumps({'type': 'query', 'filename': filename})
            s.sendall(request.encode())
            response = json.loads(s.recv(1024).decode())
            return response
    except json.JSONDecodeError:
        print(Fore.RED + "Error decoding the response from naming server.")
        return None
    except Exception as e:
        print(Fore.RED + f"Failed to contact naming server: {e}")
        return None

def send_file_to_storage_server(server_details, filename, content,username):
    server_ip, server_port = server_details.split(':')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, int(server_port)))
            message = f"PUT|{filename}|{content}|{username}"
            s.sendall(message.encode())
            
            print(Fore.GREEN +"File stored successfully")
    except Exception as e:
        print(Fore.RED + f"Error sending file to storage server: {e}")

def get_file_from_storage_server(server_details, filename,username):
    server_ip, server_port = server_details.split(':')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, int(server_port)))
            message = f"GET|{filename}||{username}"
            s.sendall(message.encode())
            response = s.recv(1024).decode()
     
            if response == 'FILE_IS_EMPTY':
                print(Fore.MAGENTA +"YOUR FILE DOES NOT HAVE CONTENT")
            else:
                with open(f'{filename}', 'w') as f:
                    f.write(response)
                    f.close()
                print(Fore.GREEN +"File saved successfully!")
                print(Fore.RESET +"File content:\n", response)
    except Exception as e:
        print(Fore.RED + f"Error retrieving file from storage server: {e}")
        
def list_all_files(server_details,username):
    server_ip, server_port = server_details.split(':')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, int(server_port)))
            message = f"LIST|||{username}"
            
            s.sendall(message.encode())
            response = s.recv(1024).decode()
            return response
    except Exception as e:
        print(Fore.RED + f"Error  No files : {e}")
        
def create_connection():
    """
    Create and return a MySQL database connection.

    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='',  # Replace with your MySQL password
            database='comp5504_users',  # Replace with your database name
        )
        
            
        return connection
    except Error as e:
        print(Fore.RED + f"Error connecting to MySQL: {e}")
        return None

def register_user():
    """
    Register a new user with a username and password.
    The password is hashed before storage for security.
    """
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")  # Securely read password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        try:
            cursor.execute(query, (username, hashed_password))
            connection.commit()
            print(Fore.GREEN +"User registered successfully!")
        except:
            print(Fore.MAGENTA +"The user already exists")
            
            
        finally:
            cursor.close()
            connection.close()

def login_user(username):
    """
    Authenticate a user by comparing the entered password (after hashing) with the stored hashed password.
    """
    
    password = getpass.getpass("Enter password: ")  # Securely read password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        try:
            cursor.execute(query, (username,))
            record = cursor.fetchone()
            if record:
                stored_password = record[0]
                if hashed_password == stored_password:
                    print(Fore.GREEN +"Login successful!")
                    return True
                else:
                    print(Fore.RED +"Password is incorrect")
            else:
                print(Fore.MAGENTA +"Username not found")
        except Error as e:
            print(Fore.RED + f"Failed to query database: {e}")
        finally:
            cursor.close()
            connection.close()
    return False

def LoginSuccess(naming_server_host, naming_server_port,username):
    
    while True:
        print(Fore.CYAN + Style.BRIGHT + "1." + Fore.GREEN + " Upload a File.")
        print(Fore.CYAN + Style.BRIGHT + "2." + Fore.GREEN + " Download a File")
        print(Fore.CYAN + Style.BRIGHT + "3." + Fore.GREEN + " List All Files.")
        print(Fore.CYAN + Style.BRIGHT + "4." + Fore.RED + " Exit.")

        operation = input("Enter Operation (1-4): ")
        if operation == '4':
            print(Fore.RED + "Exiting...")
            break

        elif operation == '3':
            server_info = contact_naming_server_for_info("",naming_server_host, naming_server_port)
            response = list_all_files(server_info['servers'][0],username)
            files = json.loads(response)
            if files == []:
                print(Fore.MAGENTA +"NO FILES TO LIST")
            else:    
                print(Fore.GREEN +"Available Files:")
                for file in files:
                    print(file)
                
        
        elif operation == '1':
            filename = input("Enter filename: ")
            try:
                with open(filename, 'r') as file:
                    content = file.read()
                    print(content)
                    file.close()
            except:
                print(Fore.MAGENTA +"File not found. Please make sure the file exists in the current directory.")

            server_info = contact_naming_server_for_info(filename, naming_server_host, naming_server_port)
            if server_info and 'servers' in server_info and server_info['servers']:
                send_file_to_storage_server(server_info['servers'][0], filename, content,username)
            else:
                print(Fore.MAGENTA +"No available storage server found.")

        elif operation == '2':
            filename = input("Enter filename: ")
            server_info = contact_naming_server_for_info(filename, naming_server_host, naming_server_port)
            if server_info and 'servers' in server_info and server_info['servers']:
              
                get_file_from_storage_server(server_info['servers'][0], filename,username)
            else:
                print(Fore.MAGENTA +"File not found on any server.")

        else:
            print(Fore.MAGENTA +"Invalid choice. Please select 1, 2, 3 or 4.")
                

def main():
    """
    Main function to drive the user interactions.
    """
    while True:
        print(Fore.CYAN + Style.BRIGHT +"Welcome to the User Management System")
        print(Fore.CYAN + Style.BRIGHT + "1." + Fore.GREEN + " Register")
        print(Fore.CYAN + Style.BRIGHT + "2." + Fore.GREEN + " Login")
        print(Fore.CYAN + Style.BRIGHT + "3." + Fore.RED + " Exit")
        choice = input("Enter choice (1-3): ")
        if choice == '1':
            
            register_user()
            
        elif choice == '2':
            username = input("Enter username: ")
            if login_user(username):
                print(Fore.CYAN + "Welcome to the DFS!")
                naming_server_host = input("Enter server host: ")
                naming_server_port = int(input("Ente server port: "))
                LoginSuccess(naming_server_host, naming_server_port,username)
            else:
                print(Fore.RED +"Failed to log in. Please try again.")
        elif choice == '3':
            print(Fore.RED + "Exiting...")
            break
        else:
            print(Fore.MAGENTA +"Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    main()

    
