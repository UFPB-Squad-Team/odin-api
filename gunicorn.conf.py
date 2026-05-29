"""
Gunicorn configuration for production deployment.
Uses Uvicorn workers for async ASGI support.
"""

import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker
# Formula: (2 * CPU cores) + 1 for I/O bound apps
# Cap at 4 for containers with limited resources
workers = min(multiprocessing.cpu_count() * 2 + 1, int(os.getenv("WEB_CONCURRENCY", "4")))
worker_class = "uvicorn.workers.UvicornWorker"
worker_tmp_dir = "/dev/shm"  # Use shared memory for heartbeat (faster in containers)

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

#Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Processing name
proc_name = "odin-api"

# Server mechanics
preload_app = True
max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
max_requests_jitter = 50  # Prevent all workers restarting at once
