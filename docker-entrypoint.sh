#!/bin/bash
set -e

# Set default environment for production
export FLASK_ENV=${FLASK_ENV:-production}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        return 0
    fi
    return 1
}

# Adjust configuration for Raspberry Pi
if is_raspberry_pi; then
    echo "Detected Raspberry Pi - applying optimizations"
    export FLASK_ENV=raspberry_pi
    export MEMORY_LIMIT_MB=512
    export PDF_GENERATION_TIMEOUT=600
    
    # Reduce Gunicorn workers for Pi
    export GUNICORN_WORKERS=2
else
    export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
fi

# Health check function
health_check() {
    echo "Performing health check..."
    if command -v curl >/dev/null 2>&1; then
        curl -f http://localhost:8000/health || exit 1
    else
        echo "curl not available, skipping health check"
    fi
}

# Start the application
echo "Starting Student Progress application..."
echo "Environment: $FLASK_ENV"
echo "Log Level: $LOG_LEVEL"
echo "Workers: $GUNICORN_WORKERS"

if [ "$1" = "dev" ]; then
    echo "Starting in development mode..."
    exec python app.py
elif [ "$1" = "gunicorn" ]; then
    echo "Starting with Gunicorn..."
    # Check if gunicorn is available
    if ! command -v gunicorn >/dev/null 2>&1; then
        echo "Gunicorn not found in PATH, trying with python -m gunicorn"
        exec python -m gunicorn --config gunicorn.conf.py --workers $GUNICORN_WORKERS wsgi:app
    else
        exec gunicorn --config gunicorn.conf.py --workers $GUNICORN_WORKERS wsgi:app
    fi
else
    # Default: start with Python (for containers)
    exec python app.py
fi
