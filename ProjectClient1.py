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
def listen_from_server(sock):
    buffer = ""
    while True:
        try:
            server_message = sock.recv(1024).decode()
            if server_message:
                buffer += server_message
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    print(message)
            else:
                print("Server closed the connection :(")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

# Send messages to the server
def send_to_server(sock):
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

# Main function to connect and handle threads
def main():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("Connected to server. Do you have an account? (Y/N)")

        # Start sending and listening threads
        send_thread = threading.Thread(target=send_to_server, args=(s,), daemon=True)
        send_thread.start()
        listen_thread = threading.Thread(target=listen_from_server, args=(s,), daemon=True)
        listen_thread.start()

        listen_thread.join()
        send_thread.join()

    except ConnectionRefusedError:
        print(f"Error: Unable to connect to {HOST}:{PORT}. Is the server running?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
