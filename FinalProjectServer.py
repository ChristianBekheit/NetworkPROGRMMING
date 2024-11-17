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
groups = {}   # Dictionary to store active group chats

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
    current_group = None
    clients[address] = {'socket': sc, 'username': None}
    
    while logged_out:
        try:
            client_message = sc.recv(1024).decode().strip()
                
            # Handle user login/registration
            if client_message == 'Y':
                sc.sendall(b'Enter your Username: \n')
                username = sc.recv(1024).decode().strip()
                
                sc.sendall(b'Enter your Password: \n')
                password = sc.recv(1024).decode().strip()
                
                if verify_credentials(username, password):
                    clients[address]['username'] = username
                    sc.sendall(b'Login successful!\nEnter a command\n')
                    logged_out = False
                else:
                    sc.sendall(b'Invalid credentials, please try again.\n')
                    continue
            
            elif client_message == 'N':
                sc.sendall(b'Would you like to register for an account? (Y/N): \n')
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
                        sc.sendall(b'Registration successful! You are now logged in.\nEnter a command\n')
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
            
            # Displays all currently online users
            if client_message == '/users':
                online_users = [info['username'] for info in clients.values() if info['username']]
                users_list = "\n".join(online_users) if online_users else "No users online."
                sc.sendall(f'\nOnline users:\n{users_list}\n'.encode())
           
            # Handle direct messaging
            elif client_message.startswith('/connect '):
                target_username = client_message.split(' ', 1)[1]
                target_client = None
                target_address = None
                
                for addr, client_info in clients.items():
                    if client_info['username'] == target_username:
                        target_client = client_info['socket']
                        target_address = addr
                        break
                
                if target_client:
                    if clients[target_address].get('connected_user'):
                        sc.sendall(f'{target_username} is already in a chat.\n'.encode())
                    else:
                        clients[address]['connected_user'] = target_client
                        clients[target_address]['connected_user'] = sc
                        sc.sendall(f'Connected to {target_username}. Type /disconnect to leave this chat. \n'.encode())
                        target_client.sendall(f'{clients[address]["username"]} has connected with you. Type /disconnect to leave this chat. \n'.encode())
                else:
                    sc.sendall(b'User not found or not online.\n')
               
                    
            connected_socket = clients[address].get('connected_user')
            if connected_socket:
                try:
                    sender_username = clients[address]["username"]
                    formatted_message = f'{sender_username}: {client_message}\n'
                    
                    connected_socket.sendall(formatted_message.encode())
                except socket.error as msg:
                    print(f'Error sending message to connected user: {msg}')
                
            elif client_message == '/disconnect':
                connected_socket = clients[address].get('connected_user')
                if connected_socket:
                    connected_socket.sendall(b'The user has disconnected from the private chat.\n')
                    clients[address]['connected_user'] = None
                    for addr, client_info in clients.items():
                        if client_info['socket'] == connected_socket:
                            clients[addr]['connected_user'] = None
                            break
                        sc.sendall(b'Disconnected from the private chat.\n')
                else:
                    sc.sendall(b'You are not connected to any user.\n')
            
            # Group chat commands
            elif client_message.startswith('/newgc '):
                group_name = client_message.split(' ', 1)[1]
                
                if group_name in groups:
                    sc.sendall(b'Group chat already exists.\n')
                else:
                    groups[group_name] = [sc]
                    current_group = group_name
                    sc.sendall(f'Group chat "{group_name}" created and joined successfully.\n'.encode())
            
            elif client_message.startswith('/join '):
                group_name = client_message.split(' ', 1)[1]
                
                if group_name not in groups:
                    sc.sendall(b'Group chat does not exist. Use /newgc to create one.\n')
                elif sc not in groups[group_name]:
                    groups[group_name].append(sc)
                    current_group = group_name
                    sc.sendall(f'Joined group chat: {group_name}\n'.encode())
                else:
                    sc.sendall(b'You are already in this group.\n')
            
            elif client_message.startswith('/leave '):
                group_name = client_message.split(' ', 1)[1]
                if group_name in groups and sc in groups[group_name]:
                    groups[group_name].remove(sc)
                    if not groups[group_name]:  # Clean up empty group
                        del groups[group_name]
                    current_group = None
                    sc.sendall(f'Left group chat: {group_name}\n'.encode())
                else:
                    sc.sendall(b'You are not in this group.\n')
                    
            elif current_group:
                # Broadcast message to all group members except the sender

                  message = f'{username} in {current_group}: {client_message}\n'
                    
                  # Broadcast message to all group members except the sender
                  for member_socket in groups[current_group]:
                        if member_socket != sc:
                            try:
                                member_socket.sendall(message.encode())
                            except socket.error as msg:
                                print(f'Error sending message to group member: {msg}')

                
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
