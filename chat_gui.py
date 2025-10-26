import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import socket
import threading
import time

class ChatClientGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("群聊客户端")
        self.window.geometry("800x600")
        
        # 连接状态
        self.connected = False
        self.socket = None
        self.in_private_chat = False
        self.in_group_chat = False
        self.current_group = None
        
        # 创建界面
        self.create_widgets()
        
        # 启动主循环
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def create_widgets(self):
        """创建所有界面组件"""
        # 顶部连接框
        self.create_connection_frame()
        
        # 聊天显示区域
        self.create_chat_display()
        
        # 输入区域
        self.create_input_frame()
        
        # 状态栏
        self.create_status_bar()
    
    def create_connection_frame(self):
        """创建连接服务器区域"""
        frame = tk.Frame(self.window, padx=10, pady=10)
        frame.pack(fill=tk.X)
        
        tk.Label(frame, text="服务器:").grid(row=0, column=0)
        self.server_entry = tk.Entry(frame, width=15)
        self.server_entry.grid(row=0, column=1)
        self.server_entry.insert(0, "127.0.0.1")
        
        tk.Label(frame, text="端口:").grid(row=0, column=2)
        self.port_entry = tk.Entry(frame, width=5)
        self.port_entry.grid(row=0, column=3)
        self.port_entry.insert(0, "12345")
        
        tk.Label(frame, text="用户名:").grid(row=0, column=4)
        self.username_entry = tk.Entry(frame, width=15)
        self.username_entry.grid(row=0, column=5)
        
        tk.Label(frame, text="密码:").grid(row=0, column=6)
        self.password_entry = tk.Entry(frame, width=15, show="*")
        self.password_entry.grid(row=0, column=7)
        
        self.connect_btn = tk.Button(frame, text="连接", command=self.connect_server)
        self.connect_btn.grid(row=0, column=8, padx=5)
        
        self.register_btn = tk.Button(frame, text="注册", command=self.register)
        self.register_btn.grid(row=0, column=9)
    
    def create_chat_display(self):
        """创建聊天显示区域"""
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_text = scrolledtext.ScrolledText(
            frame, 
            wrap=tk.WORD, 
            state='disabled',
            font=('Arial', 10)
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        
        # 设置不同消息类型的标签样式
        self.chat_text.tag_config('system', foreground='blue')
        self.chat_text.tag_config('private', foreground='purple')
        self.chat_text.tag_config('group', foreground='green')
        self.chat_text.tag_config('error', foreground='red')
    
    def create_input_frame(self):
        """创建消息输入区域"""
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.message_entry = tk.Entry(frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        
        self.send_btn = tk.Button(frame, text="发送", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        # 功能按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.private_btn = tk.Button(btn_frame, text="私聊", command=self.start_private_chat)
        self.private_btn.pack(side=tk.LEFT, padx=2)
        
        self.group_btn = tk.Button(btn_frame, text="创建群组", command=self.create_group)
        self.group_btn.pack(side=tk.LEFT, padx=2)
        
        self.join_btn = tk.Button(btn_frame, text="加入群组", command=self.join_group)
        self.join_btn.pack(side=tk.LEFT, padx=2)
        
        self.file_btn = tk.Button(btn_frame, text="发送文件", command=self.send_file)
        self.file_btn.pack(side=tk.LEFT, padx=2)
        
        self.exit_btn = tk.Button(btn_frame, text="退出", command=self.exit_chat)
        self.exit_btn.pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("状态: 未连接")
        
        status_bar = tk.Label(
            self.window, 
            textvariable=self.status_var,
            bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def connect_server(self):
        """连接服务器"""
        if self.connected:
            return
            
        server = self.server_entry.get()
        port = int(self.port_entry.get())
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server, port))
            
            # 发送登录请求
            self.socket.sendall(f"LOGIN|{username}|{password}".encode('utf-8'))
            response = self.socket.recv(1024).decode('utf-8')
            
            if response.startswith("SUCCESS"):
                self.connected = True
                self.username = username
                self.status_var.set(f"状态: 已连接 (用户: {username})")
                self.append_message("系统", "登录成功!", 'system')
                
                # 启动接收消息线程
                threading.Thread(
                    target=self.receive_messages, 
                    daemon=True
                ).start()
            else:
                self.append_message("系统", f"登录失败: {response}", 'error')
                self.socket.close()
                
        except Exception as e:
            self.append_message("系统", f"连接错误: {str(e)}", 'error')
    
    def register(self):
        """注册新账户"""
        server = self.server_entry.get()
        port = int(self.port_entry.get())
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server, port))
            
            sock.sendall(f"REGISTER|{username}|{password}".encode('utf-8'))
            response = sock.recv(1024).decode('utf-8')
            sock.close()
            
            self.append_message("系统", response, 'system')
            
        except Exception as e:
            self.append_message("系统", f"注册错误: {str(e)}", 'error')
    
    def receive_messages(self):
        """接收服务器消息"""
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                    
                if data.startswith(b"FILE_TRANSFER|"):
                    self.handle_file_transfer(data)
                    continue
                    
                data = data.decode('utf-8')
                
                if data.startswith("GROUP|"):
                    _, group, sender, msg = data.split('|', 3)
                    self.append_message(
                        f"[群组 {group}]{sender}", 
                        msg, 
                        'group'
                    )
                    
                elif data.startswith("PRIVATE|"):
                    _, sender, msg = data.split('|', 2)
                    self.append_message(
                        f"[私聊]{sender}", 
                        msg, 
                        'private'
                    )
                    
                else:
                    self.append_message("服务器", data, 'system')
                    
            except ConnectionError:
                self.append_message("系统", "连接已断开", 'error')
                self.connected = False
                break
            except Exception as e:
                self.append_message("系统", f"接收错误: {str(e)}", 'error')
                break
    
    def send_message(self):
        """发送消息"""
        if not self.connected:
            return
            
        msg = self.message_entry.get()
        if not msg:
            return
            
        try:
            self.socket.sendall(msg.encode('utf-8'))
            self.append_message("我", msg, 'system')
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            self.append_message("系统", f"发送失败: {str(e)}", 'error')
    
    def start_private_chat(self):
        """开始私聊"""
        if not self.connected:
            return
            
        target = simpledialog.askstring("私聊", "输入对方用户名:")
        if target:
            self.socket.sendall(f"@{target}".encode('utf-8'))
            self.append_message("系统", f"已请求与 {target} 私聊", 'system')
    
    def create_group(self):
        """创建群组"""
        if not self.connected:
            return
            
        group = simpledialog.askstring("创建群组", "输入群组名称:")
        if group:
            self.socket.sendall(f"# group {group}".encode('utf-8'))
            self.append_message("系统", f"已创建群组 {group}", 'system')
    
    def join_group(self):
        """加入群组"""
        if not self.connected:
            return
            
        group = simpledialog.askstring("加入群组", "输入群组名称:")
        if group:
            self.socket.sendall(f"# join {group}".encode('utf-8'))
            self.append_message("系统", f"已加入群组 {group}", 'system')
            self.in_group_chat = True
            self.current_group = group
    
    def exit_chat(self):
        """退出当前聊天"""
        if not self.connected:
            return
            
        if self.in_group_chat:
            self.socket.sendall("# exit".encode('utf-8'))
            self.append_message("系统", f"已退出群组 {self.current_group}", 'system')
            self.in_group_chat = False
            self.current_group = None
            
        elif self.in_private_chat:
            self.socket.sendall("# exit".encode('utf-8'))
            self.append_message("系统", "已退出私聊", 'system')
            self.in_private_chat = False
    
    def send_file(self):
        """发送文件"""
        if not self.connected:
            return
            
        filename = filedialog.askopenfilename(title="选择要发送的文件")
        if not filename:
            return
            
        try:
            with open(filename, 'rb') as f:
                file_data = f.read()
            
            file_info = f"{filename}|{len(file_data)}"
            header = f"FILE_START|{file_info}|FILE_END|".encode('utf-8')
            self.socket.sendall(header + file_data)
            self.append_message("系统", f"已发送文件 {filename}", 'system')
            
        except Exception as e:
            self.append_message("系统", f"发送文件失败: {str(e)}", 'error')
    
    def handle_file_transfer(self, data):
        """处理文件传输"""
        parts = data.split(b"|", 3)
        if len(parts) == 4:
            _, sender, file_info, file_data = parts
            sender = sender.decode('utf-8')
            file_info = file_info.decode('utf-8')
            
            self.append_message("系统", f"收到来自 {sender} 的文件: {file_info}", 'system')
            
            # 在实际应用中，这里应该弹出保存对话框
            # 这里简化为打印信息
            print(f"Received file: {file_info}")
    
    def append_message(self, sender, message, tag=None):
        """添加消息到聊天窗口"""
        self.chat_text.config(state='normal')
        self.chat_text.insert(tk.END, f"{sender}: {message}\n", tag)
        self.chat_text.config(state='disabled')
        self.chat_text.see(tk.END)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.connected:
            self.socket.sendall("LOGOUT".encode('utf-8'))
            self.socket.close()
        self.window.destroy()

# 启动GUI
if __name__ == "__main__":
    from tkinter import filedialog
    ChatClientGUI()