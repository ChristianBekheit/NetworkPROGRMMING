# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:23:51 2024

@author: Christian, Noah , Sam
"""

import socket
import sys
import threading

HOST = ''
PORT = 9999

CREDENTIALS_FILE = 'credentials.txt'
clients = {}  # Dictionary to store connected clients
groups = {}   # Dictionary to store active group chats

# Store user credentials in the file
def store_credentials(username, password):
    with open(CREDENTIALS_FILE, 'a') as file:
        file.write(f'{username},{password}\n')

# Check if user already exists in the credentials file
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

# Verify provided credentials against the file
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

# Handle communication with a single client
def handle_client(sc, address):
    username = None
    loggedOut = True
    current_group = None
    clients[address] = {'socket': sc, 'username': None}
    
    while loggedOut:
        try:
            client_message = sc.recv(1024).decode().strip()
                
            # Login or registration flow
            if client_message == 'Y':
                sc.sendall(b'Enter your Username: \n')
                username = sc.recv(1024).decode().strip()
                
                sc.sendall(b'Enter your Password: \n')
                password = sc.recv(1024).decode().strip()
                
                if verify_credentials(username, password):
                    clients[address]['username'] = username
                    sc.sendall(b'Login successful!\nEnter a command\n')
                    loggedOut = False
                else:
                    sc.sendall(b'Invalid credentials, please try again.\n')
                    continue
            
            elif client_message == 'N':
                sc.sendall(b'Would you like to register for an account? (Y/N): \n')
                if sc.recv(1024).decode().strip() == 'Y':
                    sc.sendall(b'Please enter your desired Username: \n')
                    username = sc.recv(1024).decode().strip()
                    
                    if user_exists(username):
                        sc.sendall(b'Username already exists. Please try a different one.\n')
                        continue
                    else:
                        sc.sendall(b'Please enter your Password: \n')
                        password = sc.recv(1024).decode().strip()
                        
                        store_credentials(username, password)
                        clients[address]['username'] = username
                        sc.sendall(b'Registration successful! You are now logged in.\nEnter a command\n')
                        loggedOut = False

                else:
                    sc.sendall(b'Registration declined. Connection closing...')
                    break
            else:
                sc.sendall(b'Invalid response, please send Y or N.\n')
                continue
        
        except socket.error as msg:
            print(f'Socket error: {msg}')
            break

    while not loggedOut:
        try:
            clientMessage = sc.recv(1024).decode().strip()
            
            # Display online users
            if clientMessage == '/users':
                online_users = [info['username'] for info in clients.values() if info['username']]
                users_list = "\n".join(online_users) if online_users else "No users online."
                sc.sendall(f'\nOnline users:\n{users_list}\n\n'.encode())
                continue
           
            # Direct messaging
            elif clientMessage.startswith('/connect '):
                targetUsername = clientMessage.split(' ', 1)[1]
                targetClient = None
                targetAddress = None
                
                for addr, clientInfo in clients.items():
                    if clientInfo['username'] == targetUsername:
                        targetClient = clientInfo['socket']
                        targetAddress = addr
                        break
                if targetClient:
                    if clients[targetAddress].get('connectedUser'):
                        sc.sendall(f'{targetUsername} is already in a chat.\n'.encode())
                    else:
                        clients[address]['connectedUser'] = targetClient
                        clients[targetAddress]['connectedUser'] = sc
                        sc.sendall(f'Connected to {targetUsername}. Type /disconnect to leave this chat. \n'.encode())
                        targetClient.sendall(f'{clients[address]["username"]} has connected with you. Type /disconnect to leave this chat. \n'.encode())
                        continue
                else:
                    sc.sendall(b'User not found or not online.\n')
                continue
            
            
            
            elif clientMessage.startswith('/list'):
                sc.sendall(f'\nUse /users, /connect <username>, /disconnect, /newgc <group>, /join <group>, /leave <group>\n\n'.encode())
                continue
            
            
            
            # Handle disconnection
            elif clientMessage == '/disconnect':
                connectedSocket = clients[address].get('connectedUser')
                if connectedSocket:
                    connectedSocket.sendall(b'The user has disconnected from the private chat.\n')
                    clients[address]['connectedUser'] = None
                    for addr, clientInfo in clients.items():
                        if clientInfo['socket'] == connectedSocket:
                            clients[addr]['connectedUser'] = None
                            break
                    sc.sendall(b'Disconnected from the private chat.\n')
                else:
                    sc.sendall(b'You are not connected to any user.\n')
                continue
            
            
            
            # Group chat commands
            elif clientMessage.startswith('/newgc '):
                group_name = clientMessage.split(' ', 1)[1]
                
                if group_name in groups:
                    sc.sendall(b'Group chat already exists.\n')
                else:
                    groups[group_name] = [sc]
                    current_group = group_name
                    sc.sendall(f'Group chat "{group_name}" created and joined successfully.\n'.encode())
                continue
            
                  
            
            elif clientMessage.startswith('/join '):
                group_name = clientMessage.split(' ', 1)[1]
                
                if group_name not in groups:
                    sc.sendall(b'Group chat does not exist. Use /newgc to create one.\n')
                elif sc not in groups[group_name]:
                    groups[group_name].append(sc)
                    current_group = group_name
                    sc.sendall(f'Joined group chat: {group_name}\n'.encode())
                else:
                    sc.sendall(b'You are already in this group.\n')
                continue
            
            
            
            elif clientMessage.startswith('/leave '):
                group_name = clientMessage.split(' ', 1)[1]
                if group_name in groups and sc in groups[group_name]:
                    groups[group_name].remove(sc)
                    if not groups[group_name]:
                        del groups[group_name]
                    current_group = None
                    sc.sendall(f'Left group chat: {group_name}\n'.encode())
                else:
                    sc.sendall(b'You are not in this group.\n')
                continue
                  
            
            
            elif current_group:
                # Broadcast to group members
                message = f'{username} in {current_group}: {clientMessage}\n'
                for member_socket in groups[current_group]:
                    if member_socket != sc:
                        try:
                            member_socket.sendall(message.encode())
                        except socket.error as msg:
                            print(f'Error sending message to group member: {msg}')
                continue
            
            connectedSocket = clients[address].get('connectedUser')
            if connectedSocket:
                try:
                    senderUsername = clients[address]["username"]
                    formattedMessage = f'{senderUsername}: {clientMessage}\n'
                
                    connectedSocket.sendall(formattedMessage.encode())
                except socket.error as msg:
                    print(f'Error sending message to connected user: {msg}')
                
            else:
                sc.sendall(b'Invalid command. Use /users, /connect <username>, /disconnect, /newgc <group>, /join <group>, /leave <group>\n')
        
        except socket.error as msg:
            print(f'Socket error: {msg}')
            break

    # Cleanup on client disconnect
    sc.close()
    del clients[address]
    for group_name in groups:
        if sc in groups[group_name]:
            groups[group_name].remove(sc)
    print(f'Connection with {address[0]}:{str(address[1])} closed')

# Setup server socket
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
        threading.Thread(target=handle_client, args=(sc, address), daemon=True).start()
    except socket.error as msg:
        print(f'Socket error: {msg}')

s.close()
sys.exit()