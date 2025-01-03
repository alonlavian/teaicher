import socket
from waitress import serve
from app import app

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

if __name__ == '__main__':
    port = find_free_port()
    print(f"\nStarting server on port {port}\n")
    serve(app, host='0.0.0.0', port=port, threads=4)
