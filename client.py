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
            data = sock.recv(1024)
            if not data:
                print("Server disconnected.")
                break
             
            # 检查是否是文件传输
            if data.startswith(b"FILE_TRANSFER|"):
                parts = data.split(b"|", 3)
                if len(parts) == 4:
                    _, sender, file_info, file_data = parts
                    sender = sender.decode('utf-8')
                    file_info = file_info.decode('utf-8')
                    
                    print(f"\n[File from {sender}]: {file_info}")
                    save_choice = input("Save this file? (Y/N): ").upper()
                    if save_choice == 'Y':
                        filename = input("Enter filename to save: ")
                        with open(filename, 'wb') as f:
                            f.write(file_data)
                        print(f"File saved as {filename}")
                    continue
                    
            data = data.decode('utf-8')
            if not data:
                print("Server disconnected.")
                break
            
            if data.startswith("GROUP|"):
                parts = data.split('|', 3)
                if len(parts) == 4:
                    _, groupname, sender, message = parts
                    print(f"[Group {groupname} from {sender}]: {message}\n")

            elif data.startswith("PRIVATE|"):
                parts = data.split('|', 2)
                if len(parts) == 3:
                    sender, message = parts[1], parts[2]
                    print(f"\n[Private from {sender}]: {message}\n")

            elif data.startswith("PRIVATE_START|"):
                sender = data.split('|')[1]
                print('*'*50,f"\nSYSTEM: {sender} started a private chat with you\n",'*'*50, end="")

            elif data.startswith("PRIVATE_END|"):
                sender = data.split('|')[1]
                print('*'*50, f"\nSYSTEM: {sender} ended the private chat\n",'*'*50, end="")

            else:
                print(f"\nServer: {data}\n", end="")

        except ConnectionError:
            print("Connection lost!")
            break


def send_file(sock, filename):
    """发送文件"""
    try:
        with open(filename, 'rb') as f:
            file_data = f.read()
        
        file_info = f"{filename}|{len(file_data)}"
        header = f"FILE_START|{file_info}|FILE_END|".encode('utf-8')
        sock.sendall(header + file_data)
        return True
    
    except Exception as e:
        print(f"Error sending file: {e}")
        return False
    

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
        in_group_chat = False
        current_group = None

        # 主线程负责发送消息
        while True:
            msg = input()
            if in_group_chat:
                if msg == "# exit":
                    sock.sendall("# exit".encode('utf-8'))
                    in_group_chat = False
                    current_group = None
                    print("Exited group chat")
                    continue
                
                sock.sendall(msg.encode('utf-8'))
                continue

            if in_private_chat:
                if msg == "# exit":
                    sock.sendall("# exit".encode('utf-8'))
                    in_private_chat = False
                    private_with = None
                    print("Exited private chat")
                    continue
                
                # 文件传输命令
                if msg.startswith("# send "):
                    print("You are sending file...")
                    filename = msg[7:]
                    if send_file(sock, filename):
                        print(f"File {filename} sent successfully")
                    else:
                        print(f"Failed to send file {filename}")
                    continue

                else:
                    sock.sendall(msg.encode('utf-8'))
                continue

            if msg.startswith("# group "):
                groupname = msg[8:]
                sock.sendall(f"# group {groupname}".encode('utf-8'))
                in_group_chat = True # 
                current_group = groupname # 
                continue
                
            if msg.startswith("# join "):
                groupname = msg[7:]
                sock.sendall(f"# join {groupname}".encode('utf-8'))
                in_group_chat = True
                current_group = groupname
                print(f"Joined group {groupname} (type '# exit' to leave)")
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