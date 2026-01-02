import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # Application settings
    TRACKER_BASE_URL = os.getenv('TRACKER_BASE_URL', 'http://localhost:5000')
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Google Sheets configuration
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    # Email configuration
    ALLOWED_DOMAINS = os.getenv('ALLOWED_DOMAINS', '').split(',') if os.getenv('ALLOWED_DOMAINS') else []
    MAX_REDIRECTS = int(os.getenv('MAX_REDIRECTS', 10))
    
    # Token configuration
    TOKEN_EXPIRY_DAYS = int(os.getenv('TOKEN_EXPIRY_DAYS', 90))
    TOKEN_LENGTH = int(os.getenv('TOKEN_LENGTH', 32))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'egor_mailer.log')
    
    # Security settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    JSON_SORT_KEYS = False
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration parameters."""
        if not cls.GOOGLE_SHEETS_ID:
            raise ValueError('GOOGLE_SHEETS_ID environment variable is required')
        
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_FILE):
            raise FileNotFoundError(f'Google credentials file not found: {cls.GOOGLE_CREDENTIALS_FILE}')
        
        return True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    GOOGLE_SHEETS_ID = 'test-sheet-id'
