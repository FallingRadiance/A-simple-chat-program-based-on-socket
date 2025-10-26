import socket

def main():
    # 创建TCP套接字（使用with语句自动管理资源）
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
        try:
            # 连接服务器（只连接一次）
            client_sock.connect(('localhost', 8000))
            print("Connected to server. Type 'exit' to quit.")
            
            while True:
                input_msg = input('You: ')
                
                if input_msg.lower() == 'exit':
                    client_sock.sendall(b'exit')  # 通知服务器关闭连接
                    break
                
                client_sock.sendall(input_msg.encode('utf-8'))
                
                response = client_sock.recv(1024)
                if not response:  # 服务器关闭连接
                    print("Server closed the connection")
                    break
                    
                print("Server:", response.decode('utf-8'))
                
        except ConnectionRefusedError:
            print("Connection refused - is server running?")
        except ConnectionResetError:
            print("Server forcibly closed the connection")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()