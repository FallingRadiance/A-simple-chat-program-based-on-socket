# 简介
一个简单的基于socket的聊天程序，包含三部分：
- simple_socket_example/
   - 一个客户端文件与服务端文件
   - 分别启动`server.py`和`client.py`后，可以在client.py的终端中输入文本，实现客户端与服务端的通信
- chat/ 
  - 一个简单的聊天程序
  - 实现了注册与登录、私聊、群聊、私聊的文件传输功能
  - 启动`server.py`和若干个`client.py`后，可以注册和登录不同的账户，实现用户间的聊天。
- chat_gui/
  - 基于tkinter库，实现了简单的图形界面
  - 功能与chat/下的程序相同