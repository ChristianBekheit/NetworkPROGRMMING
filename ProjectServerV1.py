# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:23:51 2024
@author: chris
"""

import socket
import sys

HOST = ''
PORT = 9999
CREDENTIALS_FILE = 'credentials.txt'

   
def store_credentials(username, password):
    with open(CREDENTIALS_FILE, 'a') as file:
        file.write(f'{username},{password}\n')


def user_exists(username):
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            for line in file:
                stored_username, _ = line.strip().split(',')
                if stored_username == username:
                    return True
        return False
    except FileNotFoundError:
        return False


def verify_credentials(username, password):
    try:
        with open(CREDENTIALS_FILE, 'r') as file:
            for line in file:
                stored_username, stored_password = line.strip().split(',')
                if stored_username == username and stored_password == password:
                    return True
        return False
    except FileNotFoundError:
        return False


# Setting up socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created!')

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print(f'Bind failed. Error code: {str(msg[0])} Message: {msg[1]}')
    sys.exit()

print('Socket bind complete')
s.listen(10)
print('Socket now listening...')

while True:
    try:
        sc, address = s.accept()
        print(f'Connected with {address[0]}:{str(address[1])}')

        while True:
            try:
                # Ask if the client has an account
                server_message = 'Do you have an account (Y/N): '
                sc.sendall(server_message.encode())

                client_message = sc.recv(50).decode().strip().upper()  # Get response
                if client_message == 'Y':
                    # Handle login process
                    while True:
                        sc.sendall(b'Enter your Username: ')
                        username = sc.recv(50).decode().strip()

                        sc.sendall(b'Enter your Password: ')
                        password = sc.recv(50).decode().strip()

                        if verify_credentials(username, password):
                            sc.sendall(b'Login successful!\n')
                            break  # Exit the login retry loop
                        else:
                            # Ask if they want to try again
                            sc.sendall(b'Invalid credentials, would you like to try again? (Y/N): ')
                            client_message = sc.recv(50).decode().strip().upper()

                            if client_message == 'N':
                                sc.sendall(b'Exiting program. Goodbye!\n')
                                break  # Exit the login retry loop
                    break  # Exit the main client loop after login success or exit

                elif client_message == 'N':
                    # Handle registration process
                    sc.sendall(b'Would you like to register for an account? (Y/N): ')
                    if sc.recv(50).decode().strip().upper() == 'Y':
                        sc.sendall(b'Please enter your desired Username: ')
                        username = sc.recv(50).decode().strip()

                        if user_exists(username):
                            sc.sendall(b'Username already exists. Please try a different one.\n')
                        else:
                            sc.sendall(b'Please enter your Password: ')
                            password = sc.recv(50).decode().strip()

                            store_credentials(username, password)
                            sc.sendall(b'Registration successful! You can now log in.\n')
                    else:
                        sc.sendall(b'Registration declined. Connection closing...\n')
                        break  # Exit the main client loop after declining registration
                else:
                    # Handle invalid response
                    sc.sendall(b'Invalid response, please send Y or N.\n')

            except socket.error as msg:
                print(f'Socket error: {msg}')
                break

        sc.close()  # Close connection with the client
    except socket.error as msg:
        print(f'Socket error: {msg}')
   
s.close()
sys.exit()
