import socket
import threading
# pickle 模块将复杂的 Python 对象（如列表、字典、自定义对象等）转换为字节流，这个过程称为序列化。也可以将字节流转换回原始的 Python 对象，这个过程称为反序列化。
import pickle
import os

def get_local_ip():
    # 创建一个IPv4的UDP套接字对象
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 尝试连接到一个外部地址（这里使用的是一个私有地址）
        # 实际上并不会真正建立连接，只是用于获取本地IP地址
        s.connect(('10.254.254.254', 1))
        # 获取套接字的本地地址，即本机的IP地址
        local_ip = s.getsockname()[0]
    except Exception:
        # 如果发生任何异常，使用回环地址（localhost）
        local_ip = '127.0.0.1'
    finally:
        # 关闭套接字，释放资源
        s.close()
    return local_ip

class Peer:
    def __init__(self, peer_id, server_host='10.134.195.46', server_port=65432):  # 此处server_host需要输入server此时运行的实际 IP 地址
        self.peer_id = peer_id
        self.server_host = server_host  # 中央服务器的主机地址
        self.server_port = server_port  # 中央服务器的端口
        self.resources = {}  # 储存当前节点所拥有的资源信息
        self.local_ip = get_local_ip()  # 获取本地 IP 地址
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建一个IPv4的 TCP 套接字
        self.server_socket.bind((self.local_ip, 0))  # 使用本地 IP 地址绑定服务器套接字
        self.server_socket.listen(5)  # 设置监听，最多允许 5 个节点同时连接
        self.peer_address = self.server_socket.getsockname()  # 获取对等节点的地址（IP 和端口）
        threading.Thread(target=self.listen_for_peers).start()  # 启动线程来监听其他对等节点
        self.remote_resources = {}  # 存储从其他节点获取的资源信息
        print(f"Peer {self.peer_id} started at {self.peer_address}")  # 打印当前节点的信息

        # 自动加入网络
        join_status = self.join_network()
        print(join_status)

    def join_network(self):
        # 加入P2P网络
        request = {
            'action': 'join',
            'peer_id': self.peer_id,
            'peer_address': self.peer_address
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            return "Joined network successfully"
        else:
            return "Failed to join network"

    def upload_index(self):
        # 上传资源索引到中央服务器
        request = {
            'action': 'upload_index',
            'peer_id': self.peer_id,
            'resources': list(self.resources.keys())
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            return "Uploaded index successfully"
        else:
            return "Failed to upload index"

    def retrieve_index(self):
        # 从中央服务器检索资源索引
        request = {
            'action': 'retrieve_index'
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            self.remote_resources = response['resources']
            return f"Retrieved index successfully\nResources: {response['resources']}"
        else:
            return "Failed to retrieve index"

    def leave_network(self):
        # 离开 P2P 网络
        request = {
            'action': 'leave',
            'peer_id': self.peer_id
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            return "Left network successfully"
        else:
            return "Failed to leave network"

    def send_request_to_server(self, request):
        # 发送请求到中央服务器
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_host, self.server_port))
                s.send(pickle.dumps(request))
                data = b''
                while True:
                    packet = s.recv(4096)
                    if not packet:
                        break
                    data += packet
                    if len(packet) < 4096:
                        break
                return pickle.loads(data)
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def listen_for_peers(self):
        # 监听其他对等节点的连接请求
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_peer, args=(client_socket, client_address)).start()

    def handle_peer(self, client_socket, client_address):
        # 处理其他对等节点的请求
        data = b''
        while True:
            packet = client_socket.recv(4096)
            if not packet:
                break
            data += packet
            if len(packet) < 4096:
                break
        request = pickle.loads(data)
        action = request.get('action')
        if action == 'request_resource':
            resource_name = request.get('resource_name')
            if resource_name in self.resources:
                response = {'status': 'success', 'resource': self.resources[resource_name]}
            else:
                response = {'status': 'error', 'message': 'Resource not found'}
            client_socket.send(pickle.dumps(response))
        client_socket.close()

    def request_resource_from_peer(self, resource_name):
        # 向其他对等节点请求资源
        peer_id = self.remote_resources.get(resource_name)
        if not peer_id:
            return f"Resource {resource_name} not found in network"
        peer_address = self.get_peer_address(peer_id)
        if not peer_address:
            return f"Peer {peer_id} address not found"
        print(f"Connecting to peer {peer_id} at {peer_address}")
        request = {
            'action': 'request_resource',
            'resource_name': resource_name
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer_address)
            print(f"Connected to peer {peer_id} at {peer_address}")  # 确认连接建立
            s.send(pickle.dumps(request))
            data = b''
            while True:
                try:
                    packet = s.recv(4096)
                    if not packet:
                        break
                    data += packet
                except:
                    break
            if data:
                response = pickle.loads(data)
                if response['status'] == 'success':
                    # 创建 downloaded_files 文件用于储存接收的资源文件
                    os.makedirs('downloaded_files', exist_ok=True)
                    # 写入资源文件
                    with open(os.path.join('downloaded_files', resource_name), 'wb') as file:
                        file.write(response['resource'])
                    return f"Retrieved resource {resource_name} from peer {peer_id}"
                else:
                    return f"Failed to retrieve resource {resource_name} from peer {peer_id}"
            else:
                return "No data received"

    def get_peer_address(self, peer_id):
        # 从中央服务器获取对等节点的地址
        request = {
            'action': 'retrieve_peers'
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            return response['peers'].get(peer_id)
        return None

    def add_resource(self, file_path):
        # 向当前节点添加资源
        try:
            with open(file_path, 'rb') as file:
                self.resources[os.path.basename(file_path)] = file.read()
            print(f"Added resource: {file_path}")
            # 添加资源后自动上传索引
            upload_status = self.upload_index()
            print(upload_status)
            return f"Added resource: {file_path}"
        except Exception as e:
            return f"Failed to add resource: {str(e)}"

def check_peer_id_unique(peer_id, server_host='10.134.195.46', server_port=65432):
    # 检查对等节点 ID 是否唯一
    request = {
        'action': 'retrieve_peers'
    }
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            s.send(pickle.dumps(request))
            data = b''
            while True:
                packet = s.recv(4096)
                if not packet:
                    break
                data += packet
                if len(packet) < 4096:
                    break
            response = pickle.loads(data)
            # 如果response正确返回，则进行peer_id是否重复的判定，否则返回false
            if response['status'] == 'success':
                # 如果此时输入的peer_id已经在central_server的peer列表中，则提示该peer ID已存在，返回false，否则返回true
                if peer_id in response['peers']:
                    print("Peer ID already exists. Please enter a unique Peer ID.")
                    return False
                return True
            else:
                return False
    except Exception as e:
        print(f"Error checking peer ID: {str(e)}")
        return False

def main():
    # 主函数，提供用户交互界面
    while True:
        # 提示用户输入peer ID
        peer_id = input("Enter peer ID: ")
        # 如果check_peer_id_unique检查peer_id返回true，则说明该peer_id是唯一的，即可退出while循环进行peer的初始化
        if check_peer_id_unique(peer_id):
            break
    # 初始化peer
    peer = Peer(peer_id)

    while True:
        # 让用户通过输入不同数字选择不同功能
        print("\n--------------------------------------")
        print("Options:")
        print("1. Retrieve resource index")
        print("2. Request resource from peer")
        print("3. Add resource to peer")
        print("4. Leave network")
        print("5. Exit")
        choice = input("Enter your choice: ")
        if choice == '1':
            print(peer.retrieve_index())
        elif choice == '2':
            # 让用户输入需要的资源名称
            resource_name = input("Enter the name of the resource to request: ")
            print(peer.request_resource_from_peer(resource_name))
        elif choice == '3':
            #让用户输入需要上传的资源的相对路径
            file_path = input("Enter the path of the file to add: ")
            peer.add_resource(file_path)
        elif choice == '4':
            print(peer.leave_network())
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

main()
