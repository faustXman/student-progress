"""
Configuration management for Student Progress application
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Application settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    SCHOOL_NAME = os.getenv('SCHOOL_NAME', 'Lealands High School')
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Performance settings (especially for Raspberry Pi)
    PDF_GENERATION_TIMEOUT = int(os.getenv('PDF_GENERATION_TIMEOUT', 300))  # 5 minutes
    MEMORY_LIMIT_MB = int(os.getenv('MEMORY_LIMIT_MB', 1024))
    
    # School colors (can be customized via environment)
    SCHOOL_PALETTE = [
        os.getenv('PRIMARY_COLOR', '#002147'),
        os.getenv('SECONDARY_COLOR', '#6AB023'),
        os.getenv('ACCENT_COLOR', '#4F81BD')
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'

class RaspberryPiConfig(ProductionConfig):
    """Optimized configuration for Raspberry Pi deployment"""
    MEMORY_LIMIT_MB = 512
    PDF_GENERATION_TIMEOUT = 600  # 10 minutes (slower ARM processing)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'raspberry_pi': RaspberryPiConfig,
    'default': ProductionConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'production')
    return config.get(env, config['default'])
