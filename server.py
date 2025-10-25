import socket
import threading
import json  # 用于读写字典到文件
from accounts import accounts  # 导入初始账户数据

class Server:
    def __init__(self):
        self.accounts = accounts  # 使用 accounts.py 中的数据
        self.accounts_file = "E:\\FR\\Study\\Third_Grade_first_term\\计网\\计网实验\\1017计网实验6\\chat_project\\accounts.py"  # 账户数据存储文件
        self.online_users = {}  # 在线用户字典 {username: conn}
        self.lock = threading.Lock()  # 用于线程安全操作online_users
        self.groups = {}  # 群聊字典 {groupname: {'members': [username1, username2], 'creator': username}}
        self.help_msg = '\n'+'#'*50 + '\nHELP:\nUSERS 查询当前在线用户\nLOGOUT 登出账户\n@username 实现与某用户的私聊\n# exit 退出与当前用户的私聊\n# send file_path发送文件\n# group groupname 创建群聊\n# join groupname 加入群聊\n'+'#'*50


    def create_group(self, username, groupname):
        """创建群聊"""
        with self.lock:
            if groupname in self.groups:
                return False
            self.groups[groupname] = {
                'members': [username],
                'creator': username
            }
            return True

    def join_group(self, username, groupname):
        """加入群聊"""
        with self.lock:
            if groupname not in self.groups:
                return False
            if username in self.groups[groupname]['members']:
                return False
            self.groups[groupname]['members'].append(username)
            return True

    def leave_group(self, username, groupname):
        """离开群聊"""
        with self.lock:
            if groupname not in self.groups:
                return False
            if username not in self.groups[groupname]['members']:
                return False
            self.groups[groupname]['members'].remove(username)
            return True

    def broadcast_to_group(self, groupname, message, exclude_username=None):
        """向群聊广播消息"""
        with self.lock:
            if groupname not in self.groups:
                return False
            for member in self.groups[groupname]['members']:
                if member != exclude_username and member in self.online_users:
                    try:
                        self.online_users[member].sendall(message.encode('utf-8'))
                    except ConnectionError:
                        self.remove_online_user(member)
            return True
        

    def save_accounts(self):
        """将当前账户数据保存到文件"""
        with open(self.accounts_file, "w", encoding="utf-8") as f:
            f.write(f"accounts = {json.dumps(self.accounts, indent=4)}")
    

    def broadcast(self, message, exclude_username=None):
        """向所有在线用户广播消息，可排除特定用户"""
        with self.lock:
            for username, conn in list(self.online_users.items()):
                if username != exclude_username:
                    try:
                        conn.sendall(message.encode('utf-8'))
                    except ConnectionError:
                        # 如果发送失败，移除该用户
                        self.remove_online_user(username)


    def add_online_user(self, username, conn):
        """添加用户到在线列表并广播"""
        with self.lock:
            self.online_users[username] = conn
        # 广播新用户登录信息
        self.broadcast(f"NOTICE|{username} has joined the chat", exclude_username=username)
        # 向新用户发送当前在线用户列表
        online_list = ",".join(self.get_online_users())
        response = f"\n{'*'*50}\nONLINE_USERS|[{online_list}]\n{'*'*50}\n"
        conn.sendall(response.encode('utf-8')) 



    def remove_online_user(self, username):
        """从在线列表中移除用户并广播"""
        with self.lock:
            if username in self.online_users:
                del self.online_users[username]
                # 广播用户离开信息
                notice = f"\n{'*'*50}\nNOTICE|{username} has left the chat\n{'*'*50}\n"
                self.broadcast(notice.encode('utf-8'))


    def get_online_users(self):
        """获取当前在线用户名列表"""
        with self.lock:
            return list(self.online_users.keys())
        

    def shutdown(self):
        """关闭所有连接并停止服务器"""
        print("\nShutting down server...")
        with self.lock:
            for username, conn in list(self.online_users.items()):
                try:
                    conn.sendall("NOTICE|Server is shutting down".encode('utf-8'))
                    conn.close()
                except ConnectionError:
                    pass
            self.online_users.clear()


    def handle_client(self, conn, addr):
        try:
            username = None
            in_private_chat = False
            private_with = None
            in_group_chat = False
            current_group = None

            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break

                    # 检查是否是文件传输（前12字节为FILE_START标记）
                    if data.startswith(b"FILE_START|"):
                        if not in_private_chat or not private_with:
                            conn.sendall("ERROR|File transfer only allowed in private chat".encode('utf-8'))
                            continue
                        
                        # 解析文件信息
                        header_end = data.find(b"|FILE_END|")
                        if header_end == -1:
                            continue
                        
                        file_info = data[11:header_end].decode('utf-8')  # 去掉FILE_START|
                        file_data = data[header_end+10:]  # 去掉|FILE_END|
                        
                        # 处理文件传输
                        if self.handle_file_transfer(username, private_with, file_info, file_data):
                            conn.sendall("SUCCESS|File sent successfully".encode('utf-8'))
                        else:
                            conn.sendall("ERROR|Failed to send file".encode('utf-8'))
                        continue

                    data = data.decode('utf-8')
                    print(f"Receive message from port {addr}: {data}")
                    if not data:
                        break
                    
                    if in_group_chat:
                        if data == "# exit":
                            if current_group:
                                self.leave_group(username, current_group)
                                response = f"\n{'*'*50}\nSYSTEM|You left group {current_group}\n{'*'*50}\n"
                                conn.sendall(response.encode('utf-8'))
                                in_group_chat = False
                                current_group = None
                            continue
                        
                        if data == "HELP":
                            conn.sendall(self.help_msg.encode('utf-8'))
                            continue
                        
                        if current_group:
                            # 广播消息到群聊
                            message = f"\nGROUP|{current_group}|{username}|{data}"
                            self.broadcast_to_group(
                                current_group,
                                message,
                                exclude_username=username
                            )
                        continue

                    if data.startswith("# group "):
                        groupname = data[8:]
                        if self.create_group(username, groupname):
                            response = f"\n{'*'*50}\nSYSTEM|You created group {groupname}\n{'*'*50}\n"
                            conn.sendall(response.encode('utf-8'))
                            response = f"\n{'*'*50}\nNOTICE|{username} created group {groupname}\n{'*'*50}\n"
                            self.broadcast(response)
                        else:
                            conn.sendall(f"ERROR|Group {groupname} already exists".encode('utf-8'))
                        continue

                    if data.startswith("# join "):
                        groupname = data[7:]
                        if self.join_group(username, groupname):
                            response = f"\n{'*'*50}\nSYSTEM|You joined group {groupname}\n{'*'*50}\n"
                            conn.sendall(response.encode('utf-8'))

                            in_group_chat = True
                            current_group = groupname
                            message = f"\n{'*'*50}\nNOTICE|{username} joined group {groupname}\n{'*'*50}\n"
                            self.broadcast_to_group(
                                groupname,
                                message,
                                exclude_username=username
                            )
                        else:
                            conn.sendall(f"ERROR|Group {groupname} not found or already joined".encode('utf-8'))
                        continue

                    if in_private_chat:
                        if data == "# exit":
                            if private_with:
                                self.end_private_chat(username, private_with)
                                response = f"\n{'*'*50}\nSYSTEM|Exited private chat\n{'*'*50}\n"
                                conn.sendall(response.encode('utf-8')) 
                                in_private_chat = False
                                private_with = None
                            continue
                        if data == "HELP":
                            conn.sendall(self.help_msg.encode('utf-8'))
                        if private_with:
                            self.send_private_message(username, private_with, data)
                        continue

                    if data.startswith("@"):
                        parts = data.split(maxsplit=1)
                        if len(parts) >= 1:
                            target_user = parts[0][1:]  # 去掉@符号
                            if target_user == username:
                                conn.sendall("ERROR|Cannot chat with yourself".encode('utf-8'))
                                continue
                            
                            if self.start_private_chat(username, target_user):
                                in_private_chat = True
                                private_with = target_user
                                response = f"\n{'*'*50}\nSYSTEM|Started private chat with {target_user}\n{'*'*50}\n"
                                conn.sendall(response.encode('utf-8')) 

                            else:
                                conn.sendall(f"ERROR|User {target_user} not online".encode('utf-8'))
                        continue

                    parts = data.split('|')
                    command = parts[0]

                    if command == "REGISTER":
                        username, password = parts[1], parts[2]
                        if username in self.accounts:
                            conn.sendall("ERROR|Username exists".encode('utf-8'))
                        else:
                            self.accounts[username] = password
                            self.save_accounts()  # 保存新账户到文件
                            print(f"account {username} successfully saved")
                            conn.sendall("SUCCESS|Registered".encode('utf-8'))

                    elif command == "LOGIN":
                        username, password = parts[1], parts[2]
                        if username not in self.accounts:
                            conn.sendall("ERROR|User not found".encode('utf-8'))
                        elif self.accounts[username] != password:
                            conn.sendall("ERROR|Wrong password".encode('utf-8'))
                        else:
                            conn.sendall("SUCCESS|Logged in".encode('utf-8'))
                            self.add_online_user(username, conn)
                            self.handle_authenticated_user(conn, username)

                    elif data == "LOGOUT":
                        if username:
                            self.remove_online_user(username)
                            print(f"user {username} logout")
                        break

                    elif data == "USERS":
                        print(f"Port {addr} ask online_users")
                        online_list = ",".join(self.get_online_users())
                        response = f"\n{'*'*50}\nONLINE_USERS|[{online_list}]\n{'*'*50}\n"
                        conn.sendall(response.encode('utf-8'))  # 正确写法

                    elif data == "HELP":
                            conn.sendall(self.help_msg.encode('utf-8'))

                    else:
                        conn.sendall(f"your message: {data}".encode('utf-8'))
                        print(f"Server reply port {addr}: {data} ")
                except ConnectionResetError:
                    print(f"Client {addr} forcibly closed the connection")
                    break
                except Exception as e:
                    print(f"Error with client {addr}: {str(e)}")
                    break

        finally:
            # 确保资源被释放
            print(f"Cleaning up connection for {addr}")
            if username and current_group:
                self.leave_group(username, current_group)
            if username:
                self.remove_online_user(username)
            try:
                conn.shutdown(socket.SHUT_RDWR)  # 完全关闭连接
            except:
                pass
            conn.close()
            print(f"Connection for {addr} fully closed")


    def handle_authenticated_user(self, conn, username):
        """已登录用户的主逻辑"""
        conn.sendall(f"Welcome, {username}!\nEnter 'HELP' to read help message".encode('utf-8'))


    def send_private_message(self, sender, receiver, message):
        """发送私聊消息"""
        with self.lock:
            if receiver in self.online_users:
                try:
                    self.online_users[receiver].sendall(
                        f"PRIVATE|{sender}|{message}".encode('utf-8')
                    )
                    return True
                except ConnectionError:
                    self.remove_online_user(receiver)
            return False
        

    def start_private_chat(self, sender, receiver):
        """开始私聊"""
        with self.lock:
            if receiver in self.online_users:
                try:
                    self.online_users[receiver].sendall(
                        f"PRIVATE_START|{sender}".encode('utf-8')
                    )
                    return True
                except ConnectionError:
                    self.remove_online_user(receiver)
            return False


    def end_private_chat(self, sender, receiver):
        """结束私聊"""
        with self.lock:
            if receiver in self.online_users:
                try:
                    self.online_users[receiver].sendall(
                        f"PRIVATE_END|{sender}".encode('utf-8')
                    )
                    return True
                except ConnectionError:
                    self.remove_online_user(receiver)
            return False
        

    def handle_file_transfer(self, sender, receiver, file_info, file_data):
        """处理文件传输"""
        with self.lock:
            if receiver in self.online_users:
                try:
                    # 发送文件信息和数据给接收方
                    self.online_users[receiver].sendall(
                        f"FILE_TRANSFER|{sender}|{file_info}".encode('utf-8') + file_data
                    )
                    return True
                except ConnectionError:
                    self.remove_online_user(receiver)
            return False
        

    def run_server(self):
        print("server is running...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 允许端口重用
        server.bind(('0.0.0.0', 12345))
        server.listen()
        print("listening port 12345...")

        try:
            while True:
                conn, addr = server.accept()
                print(f"Port {addr} connected!")

                # 创建线程并设置为守护线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True  # 关键修复：设置为守护线程
                )
                client_thread.start()

        except KeyboardInterrupt:
            print("\nServer is shutting down...")
        finally:
            self.shutdown()
            server.close()


if __name__ == "__main__":
    server = Server()
    server.run_server()