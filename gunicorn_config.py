import multiprocessing
import socket

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

# Server socket
port = find_free_port()
bind = f"0.0.0.0:{port}"
backlog = 2048

# Print the port for user reference
print(f"\nServer starting on port {port}\n")

# Worker processes
workers = 2  # Reduced number of workers for stability
worker_class = 'gevent'  # Using gevent for better stability
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'  # Increased log level for debugging

# Process naming
proc_name = 'teaicher'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Prevent memory leaks
max_requests = 1000
max_requests_jitter = 50
