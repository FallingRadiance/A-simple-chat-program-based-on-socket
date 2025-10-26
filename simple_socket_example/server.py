import socket

def handle_client(conn, addr):
    """处理单个客户端连接的完整会话"""
    try:
        conn.settimeout(10)  # 设置稍长的超时
        print(f"\nClient {addr} connected")
        
        while True:  # 持续对话循环
            data = conn.recv(1024)
            if not data:
                print(f"Client {addr} disconnected")
                break
                
            msg = data.decode('utf-8')
            print(f"Received: {msg}")
            
            if msg.lower() == 'exit':
                conn.sendall(b'Goodbye!')
                break
                
            # 业务逻辑处理
            response = process_message(msg)
            conn.sendall(response.encode('utf-8'))
            
    except socket.timeout:
        print(f"Client {addr} timeout")
    except ConnectionResetError:
        print(f"Client {addr} forcibly closed")
    finally:
        conn.close()  # 确保连接关闭
        print(f"Connection with {addr} closed")

def process_message(msg):
    """示例业务逻辑"""
    if msg == '1':
        return "Welcome to server!"
    elif msg == 'date':
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        return f"You said: {msg}"

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('localhost', 8000))
        server_sock.listen(5)
        print("Server ready on port 8000...")
        
        while True:
            conn, addr = server_sock.accept()
            handle_client(conn, addr)  # 处理每个新连接

if __name__ == '__main__':
    main()