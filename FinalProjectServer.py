
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:23:51 2024

@author: christian, Noah
""" 

import socket
import sys
import threading

HOST = ''
PORT = 9999

CREDENTIALS_FILE = 'credentials.txt'
clients = {}  # Dictionary to store connected clients

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
        with open(CREDENTIALS_FILE, 'r') as  file:
            for line in file:
                stored_username, stored_password = line.strip().split(',')
                if stored_username == username and stored_password == password:
                    return True
        return False
    except FileNotFoundError:
        return False

def handle_client(sc, address):
    username = None
    connected_user = None
    logged_out = True
    clients[address] = {'socket': sc, 'username': None}
    
    while logged_out:
        try:
            # Ask if the client has an account
            sc.sendall(b'Do you have an account (Y/N): ')
            client_message = sc.recv(1024).decode().strip()
                
            # Handle user login/registration
            if client_message == 'Y':
                sc.sendall(b'Enter your Username: ')
                username = sc.recv(1024).decode().strip()
                
                sc.sendall(b'Enter your Password: ')
                password = sc.recv(1024).decode().strip()
                
                if verify_credentials(username, password):
                    clients[address]['username'] = username
                    sc.sendall(b'Login successful!\n')
                    logged_out = False
                else:
                    sc.sendall(b'Invalid credentials, please try again.\n')
                    continue
            
            elif client_message == 'N':
                sc.sendall(b'Would you like to register for an account? (Y/N): ')
                if sc.recv(1024).decode().strip() == 'Y':
                    sc.sendall(b'Please enter your desired Username: ')
                    username = sc.recv(1024).decode().strip()
                    
                    if user_exists(username):
                        sc.sendall(b'Username already exists. Please try a different one.\n')
                        continue
                    else:
                        sc.sendall(b'Please enter your Password: ')
                        password = sc.recv(1024).decode().strip()
                        
                        store_credentials(username, password)
                        clients[address]['username'] = username
                        sc.sendall(b'Registration successful! You can now log in.')
                        logged_out = False
                else:
                    sc.sendall(b'Registration declined. Connection closing...')
                    break
            else:
                sc.sendall(b'Invalid response, please send Y or N.\n')
                continue
        
        except socket.error as msg:
            print(f'Socket error: {msg}')
            break

    while not logged_out:
        try:
            client_message = sc.recv(1024).decode().strip()
            
            
            # Handle direct messaging
            if client_message.startswith('/connect '):
                target_username = client_message.split(' ', 1)[1]
                target_client = None
                for client_info in clients.values():
                    if client_info['username'] == target_username:
                        target_client = client_info['socket']
                        break
                
                
                if target_client:
                    sc.sendall(f'Connected to {target_username}. You can now chat.'.encode())
                    connected_user = target_client
                else:
                    sc.sendall(b'User not found or not online.\n')
                    
                    
            elif client_message == '/disconnect':
                if connected_user:
                    connected_user.sendall(b'The user has disconnected from the chat.\n')
                    connected_user = None
                    sc.sendall(b'Disconnected from chat.\n')
                else:
                    sc.sendall(b'You are not connected to any user.\n')
                    
                    
            elif connected_user:
                # Forwards message to the connected user
                connected_user.sendall(f'{username}: {client_message}\n'.encode())
            else:
                sc.sendall(b'You are not connected to any user. Use /connect <username> to start chatting.\n')
        
        
        except socket.error as msg:
            print(f'Socket error: {msg}')
            break

    sc.close()
    del clients[address]
    print(f'Connection with {address[0]}:{str(address[1])} closed')

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
        threading.Thread(target=handle_client, args=(sc, address)).start()
    except socket.error as msg:
        print(f'Socket error: {msg}')

s.close()
sys.exit()
