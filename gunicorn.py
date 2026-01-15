"""Gunicorn configuration file for production."""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Process naming
proc_name = "zendesk-dashboard"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "zendesk-dashboard"

# Worker tmp directory (use memory for better performance)
worker_tmp_dir = "/dev/shm"

# Preload app for better performance
preload_app = True

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Gunicorn server starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Gunicorn server reloading...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Gunicorn server is ready. Serving on {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker exited (pid: {worker.pid})")