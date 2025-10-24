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
        conn.sendall(response.encode('utf-8'))  # 正确写法



    def remove_online_user(self, username):
        """从在线列表中移除用户并广播"""
        with self.lock:
            if username in self.online_users:
                del self.online_users[username]
                # 广播用户离开信息
                self.broadcast(f"NOTICE|{username} has left the chat")


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
            while True:
                data = conn.recv(1024).decode('utf-8')
                print(f"Receive message from port {addr}: {data} ")
                if not data:
                    break

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

                elif data == "who online":
                    print(f"Port {addr} ask online_users")
                    online_list = ",".join(self.get_online_users())
                    response = f"\n{'*'*50}\nONLINE_USERS|[{online_list}]\n{'*'*50}\n"
                    conn.sendall(response.encode('utf-8'))  # 正确写法

                else:
                    conn.sendall(f"your message: {data}".encode('utf-8'))
                    print(f"Server reply port {addr}: {data} ")

        except ConnectionError:
            print(f"warning: 客户端{addr}异常断开")
        finally:
            if username:
                self.remove_online_user(username)
            conn.close()


    def handle_authenticated_user(self, conn, username):
        """已登录用户的主逻辑"""
        conn.sendall(f"Welcome, {username}!".encode('utf-8'))


    def run_server(self):
        print("server is running...")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', 12345))
        server.listen()
        print("listening port 12345...")

        try:
            while True:
                conn, addr = server.accept()
                print(f"Port {addr} connected!")
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            print("\nServer is shutting down...")
        finally:
            self.shutdown()
            server.close()


if __name__ == "__main__":
    server = Server()
    server.run_server()