import socket
import threading
import pickle
import os

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

class Peer:
    def __init__(self, peer_id, server_host='10.134.116.137', server_port=65432):
        self.peer_id = peer_id
        self.server_host = server_host
        self.server_port = server_port
        self.resources = {}
        self.local_ip = get_local_ip()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.local_ip, 0))
        self.server_socket.listen(5)
        self.peer_address = self.server_socket.getsockname()
        threading.Thread(target=self.listen_for_peers).start()
        self.remote_resources = {}
        print(f"Peer {self.peer_id} started at {self.peer_address}")

    def join_network(self):
        request = {
            'action': 'join',
            'peer_id': self.peer_id,
            'peer_address': self.peer_address
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            print("Joined network successfully")
            return "Joined network successfully"
        else:
            print("Failed to join network")
            return "Failed to join network"

    def upload_index(self):
        request = {
            'action': 'upload_index',
            'peer_id': self.peer_id,
            'resources': list(self.resources.keys())
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            print("Uploaded index successfully")
            return "Uploaded index successfully"
        else:
            print("Failed to upload index")
            return "Failed to upload index"

    def retrieve_index(self):
        request = {
            'action': 'retrieve_index'
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            print("Retrieved index successfully")
            print("Resources:", response['resources'])
            self.remote_resources = response['resources']
            return f"Retrieved index successfully\nResources: {response['resources']}"
        else:
            print("Failed to retrieve index")
            return "Failed to retrieve index"

    def leave_network(self):
        request = {
            'action': 'leave',
            'peer_id': self.peer_id
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            print("Left network successfully")
            return "Left network successfully"
        else:
            print("Failed to leave network")
            return "Failed to leave network"

    def send_request_to_server(self, request):
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
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_peer, args=(client_socket, client_address)).start()

    def handle_peer(self, client_socket, client_address):
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
        peer_id = self.remote_resources.get(resource_name)
        if not peer_id:
            print(f"Resource {resource_name} not found in network")
            return f"Resource {resource_name} not found in network"
        peer_address = self.get_peer_address(peer_id)
        if not peer_address:
            print(f"Peer {peer_id} address not found")
            return f"Peer {peer_id} address not found"
        request = {
            'action': 'request_resource',
            'resource_name': resource_name
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer_address)
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
                    print(f"Retrieved resource {resource_name} from peer {peer_id}")
                    os.makedirs('downloaded_files', exist_ok=True)
                    with open(os.path.join('downloaded_files', resource_name), 'wb') as file:
                        file.write(response['resource'])
                    return f"Retrieved resource {resource_name} from peer {peer_id}"
                else:
                    print(f"Failed to retrieve resource {resource_name} from peer {peer_id}")
                    return f"Failed to retrieve resource {resource_name} from peer {peer_id}"
            else:
                return "No data received"

    def get_peer_address(self, peer_id):
        request = {
            'action': 'retrieve_peers'
        }
        response = self.send_request_to_server(request)
        if response['status'] == 'success':
            return response['peers'].get(peer_id)
        return None

    def add_resource(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                self.resources[os.path.basename(file_path)] = file.read()
            print(f"Added resource: {file_path}")
            return f"Added resource: {file_path}"
        except Exception as e:
            return f"Failed to add resource: {str(e)}"

def main():
    peer_id = input("Enter peer ID: ")
    peer = Peer(peer_id)

    while True:
        print("\nOptions:")
        print("1. Join network")
        print("2. Upload resource index")
        print("3. Retrieve resource index")
        print("4. Request resource from peer")
        print("5. Add resource to peer")
        print("6. Leave network")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            print(peer.join_network())
        elif choice == '2':
            print(peer.upload_index())
        elif choice == '3':
            print(peer.retrieve_index())
        elif choice == '4':
            resource_name = input("Enter the name of the resource to request: ")
            print(peer.request_resource_from_peer(resource_name))
        elif choice == '5':
            file_path = input("Enter the path of the file to add: ")
            print(peer.add_resource(file_path))
        elif choice == '6':
            print(peer.leave_network())
        elif choice == '7':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()