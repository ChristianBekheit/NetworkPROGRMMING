# -*- coding: utf-8 -*-#
"""
Created on Mon Sep 23 10:00:05 2024

@author: chris, noah , sam
"""

import socket
import threading

HOST = 'localhost'  # localhost 
PORT = 9999

def listenFromServer(sock):
    buffer = ""  
    while True:
        try:
            server_message = sock.recv(1024).decode()
            if server_message:
                buffer += server_message
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    print(f'{message}')
            else:
                print("Server closed the connection :(")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break
            
def sendToServer(sock):
    while True:
        try:
            client_message = input("")
            sock.sendall((client_message + "\n").encode())
            if client_message.lower() == '/disconnect':
                print("Closing connection...")
                break
        except Exception as e:
            print(f"Error sending message to server: {e}")
            break
            
def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("Connected to server. Do you have an account? (Y/N)")
        
        # Thread for sending so the client can send simultaneously
        send_thread = threading.Thread(target=sendToServer, args=(s,), daemon=True)
        send_thread.start()
        
        # Opens the thread for the listening function, so the client is always listening
        listen_thread = threading.Thread(target=listenFromServer, args=(s,), daemon=True)
        listen_thread.start()

        listen_thread.join()
        send_thread.join()
    except ConnectionRefusedError as e:
        # here is the error handling for if the server is unavailable
        print(f"Error: Unable to connect to the server at {HOST}:{PORT}. Is the server running?")
    except Exception as e:
        # here is the handling for general connection errors
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
