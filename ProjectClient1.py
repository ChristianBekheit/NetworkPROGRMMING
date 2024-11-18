# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:00:05 2024

@author: Christian, Noah, Sam
"""

import socket
import threading

HOST = 'localhost'
PORT = 9999

# Listen for messages from the server
def listenFromServer(sock):
    while True:
        try:
            serverMessage = sock.recv(1024).decode()
            if serverMessage:
                    print(serverMessage)
            else:
                print("Server closed the connection :(")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Send messages to the server
def sendToServer(sock):
    while True:
        try:
            clientMessage = input("")
            sock.sendall((clientMessage + "\n").encode())
            if clientMessage.lower() == '/disconnect':
                print("Closing connection...")
                break
        except Exception as e:
            print(f"Error sending message to server: {e}")
            break

# Main function to connect and handle threads
def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("Connected to server. Do you have an account? (Y/N)")

        # Start sending and listening threads
        sendThread = threading.Thread(target=sendToServer, args=(s,), daemon=True)
        sendThread.start()
        listenThread = threading.Thread(target=listenFromServer, args=(s,), daemon=True)
        listenThread.start()

        listenThread.join()
        sendThread.join()

    except ConnectionRefusedError:
        print(f"Error: Unable to connect to {HOST}:{PORT}. Is the server running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
