# import os
# import secrets

# from dotenv import load_dotenv

# load_dotenv()


# class BaseConfig(object):
#     basedir = os.path.abspath(os.path.dirname(__file__))
#     DEBUG = False


# class DevelopmentConfig(BaseConfig):
#     FLASK_ENV = "development"
#     ITEMS_PER_PAGE = 1000
#     SECRET_KEY = os.getenv("SECRET_KEY", str(secrets.token_hex()))
#     SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///site.db")
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
#     CORS_ORIGIN = ["http://localhost:3000", "*"]
#     CORS_ALLOW_HEADERS = "*"
#     CORS_AUTOMATIC_OPTIONS = True


# class StagingConfig(BaseConfig):
#     FLASK_ENV = "production"
#     ITEMS_PER_PAGE = 1000
#     SECRET_KEY = os.getenv("SECRET_KEY")
#     SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     CORS_METHODS = ["POST", "PUT", "GET", "OPTIONS", "DELETE"]
#     CORS_ORIGIN = ["http://localhost:3000", "*"]
#     CORS_ALLOW_HEADERS = "*"
#     CORS_AUTOMATIC_OPTIONS = True


# class TestingConfig(BaseConfig):
#     DEBUG = True
#     FLASK_ENV = "testing"



import os
from datetime import timedelta
from typing import Type


class Config:
    """Base configuration class"""
    
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///campmanager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    JWT_ERROR_MESSAGE_KEY = 'message'
    PROPAGATE_EXCEPTIONS = True
    
    # APIFlask config
    OPENAPI_VERSION = '3.0.2'
    INFO = {
        'title': 'CampManager API',
        'version': '1.0.0',
        'description': 'A comprehensive camp management system API for church camps'
    }
    TAGS = [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Camps', 'description': 'Camp management operations'},
        {'name': 'Churches', 'description': 'Church management operations'},
        {'name': 'Categories', 'description': 'Registration category management'},
        {'name': 'Custom Fields', 'description': 'Dynamic form field management'},
        {'name': 'Registration Links', 'description': 'Category-specific registration links'},
        {'name': 'Registrations', 'description': 'Registration management'},
        {'name': 'Public', 'description': 'Public registration endpoints'}
    ]
    SERVERS = [
        {'url': 'http://localhost:5000', 'description': 'Development server'},
        {'url': 'https://api.campmanager.com', 'description': 'Production server'}
    ]
    
    # Security config
    WTF_CSRF_ENABLED = False  # Disabled for API
    JSON_SORT_KEYS = False
    
    # File upload config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    # Logging config
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    
    # CORS config
    CORS_ORIGINS = ['*']
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    PROPAGATE_EXCEPTIONS = True
    
    # Relaxed CORS for development
    CORS_ORIGINS = ['*']
    
    # Development database
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///campmanager.db')
    
    # Development JWT config (shorter expiry for testing)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Set up console logging for development
        
        


class TestingConfig(Config):
    """Testing configuration"""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Shorter JWT expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Test secret keys
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', '')
    
    # Enhanced security in production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30
    }
    
    # Production CORS (specific origins)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Production logging
    LOG_LEVEL = 'DEBUG'
    # LOG_FILE = os.environ.get('LOG_FILE') or '/var/log/campmanager/app.log'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        
       

class DockerConfig(ProductionConfig):
    """Docker container configuration"""
    
    # Docker-specific database URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    # Container logging (to stdout)
    LOG_FILE = None
    
    @staticmethod
    def init_app(app):
        ProductionConfig.init_app(app)
        
        # Log to stdout in containers
        import logging
        import sys
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Type[Config]:
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    return config.get(config_name, DevelopmentConfig)
