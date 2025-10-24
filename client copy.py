import socket
import threading
import time


def register(username, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 12345))
    sock.sendall(f"REGISTER|{username}|{password}".encode('utf-8'))
    response = sock.recv(1024).decode('utf-8')
    sock.close()
    return response

def receive_messages(sock):
    """持续接收服务器消息的线程函数"""
    while True:
        try:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("Server disconnected.")
                break
            print(f"\nServer: {data}\n")  # 保持输入提示
        except ConnectionError:
            print("Connection lost!")
            break

def login(username, password):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 12345))
    sock.sendall(f"LOGIN|{username}|{password}".encode('utf-8'))
    response = sock.recv(1024).decode('utf-8')
    
    if response.startswith("SUCCESS"):
        print("Login successful!")
        # 启动接收消息的线程
        recv_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
        recv_thread.start()
        
        # 主线程负责发送消息
        while True:
            time.sleep(0.2)
            msg = input("Enter message: ")
            if msg.lower() == 'logout':
                print("You logout")
                break
            sock.sendall(msg.encode('utf-8'))

            
        
        sock.close()
    else:
        print("Login failed:", response)
        sock.close()

while True:
    action = input("Register (R) or Login (L) or exit (E)? ").upper()
    if action == "E":
        break
        
    username = input("Username: ")
    password = input("Password: ")

    if action == "R":
        print(register(username, password))
    elif action == "L":
        login(username, password)
    else:
        print("Invalid choice")