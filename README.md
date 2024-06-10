# SCU-CN-2024-SW-Project
一、开发环境
操作系统：macOS Ventura 13.2.1 (22D68)、Window 11
编程语言：Python 3.8.3 (v3.8.3:6f8c8320e9, May 13 2020, 16:29:34) 
[Clang 6.0 (clang-600.0.57)] on darwin
网络协议：TCP/IP
网络编程库：Python socket 库

二、开发工具
集成开发环境（IDE）：Visual Studio Code版本: 1.89.1 (Universal)
版本控制：Git

三、系统设计架构
系统概述： 本系统是一个基于 TCP 的对等（P2P）资源共享系统，允许用户在局域网内或通过互联网共享和获取文件资源。

主要组件：
1、中央服务器（Central Server）：
1.负责管理所有对等节点的信息。
2.处理对等节点的加入和离开请求。
3.提供对等节点资源索引的检索服务。
2、对等节点（Peer）：
1.既是客户端也是服务器，能够请求和提供资源。
2.启动时自动加入网络并注册自己的资源。
3.支持资源的动态添加和检索。
流程说明：
1、对等节点启动时，自动连接到中央服务器并注册自身信息。
2、对等节点可以动态添加资源，并自动将资源索引上传到中央服务器。
3、对等节点可以从中央服务器检索资源索引，并直接与拥有资源的对等节点建立连接以获取资源。

四、系统的安装和用户手册
安装步骤：
1、克隆项目代码：
git clone <项目仓库地址>
cd <项目目录>
2、安装 Python 3.9：
确保系统已安装 Python 3.9。可以从 Python 官方网站 下载并安装。
3、安装 netifaces：
netifaces：用于获取网络接口信息。
需要使用 pip 来安装 netifaces 包。在安装了 Python 3.9 后，可以通过以下命令安装 netifaces：
pip install netifaces
4、运行中央服务器：
在一台机器上运行中央服务器：
python central_server.py
5、运行对等节点：
在每个对等节点机器上运行以下命令启动对等节点：
python peer.py
用户手册：
1、启动对等节点：
用户打开 peer.py 文件，输入需要连接的Central Server的server host和server port，输入唯一的 peer ID，系统将自动加入网络。
2、添加资源：
用户选择 Add resource to peer 选项，输入文件路径，系统将自动上传资源索引到中央服务器。
3、检索资源：
用户选择 Retrieve resource index 选项，系统将从中央服务器获取所有可用资源的索引。
用户选择 Request resource from peer 选项，输入资源名称，系统将从拥有该资源的对等节点获取资源。
4、离开网络：
用户选择 Leave network 选项，系统将从中央服务器注销，并关闭连接。
