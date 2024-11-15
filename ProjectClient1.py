# -*- coding: utf-8 -*-#
"""
Created on Mon Sep 23 10:00:05 2024

@author: chris, noah , sam
"""

import socket
import threading

HOST = 'localhost'#localhost 
PORT = 9999





def listenFromServer(sock):
        while True:
            try:
                server_message = sock.recv(1024).decode()
                if server_message:
                    print(f'Server: {server_message}')
                else:
                    print("Server closed the connection :(")
                    break
            except Exception as e:
                print(f"Error recieving message: {e}")
                break
            
            
def sendToServer(sock):
        while True:
            try:
                client_message = input("Me: ")
                sock.sendall(client_message.encode())
                if client_message.lower() == '/disconnect':
                    print("Closing connection...")
                    break
            except Exception as e:
                print(f"Error sending message to server: {e}")
                break
            
def main():

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        print("Connected to server.")
        
        #thread for sending so the client can send simultaenuoysly
        send_thread = threading.Thread(target=sendToServer, args=(s,))
        send_thread.start()
        
        #opens the thread for the listening function, so the client is always listening
        listen_thread = threading.Thread(target=listenFromServer, args=(s,))
      
        listen_thread.start()

        listen_thread.join()
        send_thread.join()
        
    
    
   