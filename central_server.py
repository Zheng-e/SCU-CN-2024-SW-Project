import socket
import threading
import pickle

class CentralServer:
    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.peers = {}
        self.resources = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.host, self.port))
        except OSError as e:
            if e.errno == 48:
                print(f"Port {self.port} is already in use. Please use a different port.")
                exit(1)
        self.server_socket.listen(5)
        print(f"Central server started at {self.host}:{self.port}")

    def handle_client(self, client_socket, client_address):
        data = b''
        while True:
            try:
                packet = client_socket.recv(4096)
                if not packet:
                    break
                data += packet
                if len(packet) < 4096:
                    break
            except ConnectionResetError:
                break
        try:
            request = pickle.loads(data)
            response = self.process_request(request)
            client_socket.send(pickle.dumps(response))
        except pickle.UnpicklingError as e:
            print(f"Unpickling error: {e}")
        client_socket.close()

    def process_request(self, request):
        action = request.get('action')
        if action == 'join':
            return self.join_network(request)
        elif action == 'upload_index':
            return self.upload_index(request)
        elif action == 'retrieve_index':
            return self.retrieve_index(request)
        elif action == 'leave':
            return self.leave_network(request)
        elif action == 'retrieve_peers':
            return self.retrieve_peers(request)
        else:
            return {'status': 'error', 'message': 'Unknown action'}

    def join_network(self, request):
        peer_id = request.get('peer_id')
        peer_address = request.get('peer_address')
        self.peers[peer_id] = peer_address
        return {'status': 'success', 'peers': self.peers}

    def upload_index(self, request):
        peer_id = request.get('peer_id')
        resources = request.get('resources')
        for resource in resources:
            self.resources[resource] = peer_id
        return {'status': 'success'}

    def retrieve_index(self, request):
        return {'status': 'success', 'resources': self.resources}

    def leave_network(self, request):
        peer_id = request.get('peer_id')
        if peer_id in self.peers:
            del self.peers[peer_id]
        resources_to_remove = [resource for resource, owner in self.resources.items() if owner == peer_id]
        for resource in resources_to_remove:
            del self.resources[resource]
        return {'status': 'success'}

    def retrieve_peers(self, request):
        return {'status': 'success', 'peers': self.peers}

    def run(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

if __name__ == '__main__':
    server = CentralServer()
    server.run()
