from multiprocessing import cpu_count
import os

# Localhost bind target (override with GUNICORN_BIND if needed).
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:5001")

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = os.environ.get("GUNICORN_ACCESSLOG", "gunicorn_access.log")
errorlog = os.environ.get("GUNICORN_ERRORLOG", "gunicorn_error.log")
