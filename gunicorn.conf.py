"""
Gunicorn configuration for production deployment.
Uses Uvicorn workers for async ASGI support.
"""

import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker
# One async worker keeps independent process heaps within 512 MB.
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
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
preload_app = False
max_requests = int(os.getenv("MAX_REQUESTS", "1000"))
max_requests_jitter = 50  # Prevent all workers restarting at once


def on_starting(server):
    server.log.info("runtime workers=%s preload_app=%s", server.cfg.workers, server.cfg.preload_app)
