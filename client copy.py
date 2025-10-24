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
                
            if data.startswith("PRIVATE|"):
                parts = data.split('|', 2)
                if len(parts) == 3:
                    sender, message = parts[1], parts[2]
                    print(f"\n[Private from {sender}]: {message}\n", end="")
            elif data.startswith("PRIVATE_START|"):
                sender = data.split('|')[1]
                print(f"\nSYSTEM: {sender} started a private chat with you\n", end="")
            elif data.startswith("PRIVATE_END|"):
                sender = data.split('|')[1]
                print(f"\nSYSTEM: {sender} ended the private chat\n", end="")
            else:
                print(f"\nServer: {data}\n", end="")
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
        
        in_private_chat = False
        private_with = None
        
        # 主线程负责发送消息
        while True:
            msg = input("Enter message: ")
            
            if in_private_chat:
                if msg == "# exit":
                    sock.sendall("# exit".encode('utf-8'))
                    in_private_chat = False
                    private_with = None
                    print("Exited private chat")
                    continue
                
                sock.sendall(msg.encode('utf-8'))
                continue
            
            if msg.startswith("@"):
                target_user = msg[1:].split()[0] if len(msg) > 1 else ""
                if target_user:
                    sock.sendall(msg.encode('utf-8'))
                    in_private_chat = True
                    private_with = target_user
                    print(f"Started private chat with {target_user} (type '# exit' to end)")
                continue
            
            if msg.lower() == 'logout':
                sock.sendall("LOGOUT".encode('utf-8'))
                print("You logged out")
                break
                
            sock.sendall(msg.encode('utf-8'))
            
        sock.close()
    else:
        print("Login failed:", response)
        sock.close()

while True:
    action = input("Register (R) or Login (L) or exit (E)? ").upper()
    if not (action == 'E' or 'R' or "L"):
        print("Invalid choice")
        continue

    if action == "E":
        print("Exit successfullly!")
        break
        
    username = input("Username: ")
    password = input("Password: ")

    if action == "R":
        print(register(username, password))
    elif action == "L":
        login(username, password)
    else:
        print("Invalid choice")