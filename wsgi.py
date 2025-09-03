"""
WSGI entry point for production deployment
"""
from app import app
from config import get_config
import logging

# Get configuration
config_class = get_config()
config_instance = config_class()

# Configure app for production
app.config.from_object(config_instance)

# Set up logging for production
if not app.debug:
    logging.basicConfig(
        level=getattr(logging, config_instance.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

if __name__ == "__main__":
    app.run()
