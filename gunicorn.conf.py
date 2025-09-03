"""
Gunicorn configuration for production deployment
Optimized for Raspberry Pi 4B and general production use
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Limit for Pi
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes for PDF generation
keepalive = 2

# Memory management (important for Pi)
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = '-'
errorlog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'student-progress'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
