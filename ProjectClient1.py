# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 10:08:14 2024

@author: chris
"""

# -*- coding: utf-8 -*-#
"""
Created on Mon Sep 23 10:00:05 2024

@author: chris
"""

import socket

HOST = '10.220.33.104'#localhost 
PORT = 9999

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST,PORT))

while True:
   
    
    # Receive the server's response
    server_message = s.recv(1024).decode()
    print(f'Server: {server_message}')
    
    # Get the client's message from the console input
    client_message = input('Client: ')
    
    # Send the client's message to the server
    s.sendall(client_message.encode())
    
    # Check if the server's message is 'end', then break the loop and close connection
    if client_message == 'end':
        print("Client has ended the conversation.")
        break

# Close the socket connection
s.close()
