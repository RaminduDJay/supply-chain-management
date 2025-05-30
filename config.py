"""
Supply Chain Management System - Configuration
Application configuration settings for different environments.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'supply_chain_db')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'supply_chain:'
    SESSION_COOKIE_NAME = 'supply_chain_session'
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Security configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False  # Set to True in production with HTTPS
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'csv'}
    
    # Email configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@supplychain.lk')
    
    # Redis configuration (for caching and sessions)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # Pagination configuration
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # API configuration
    API_RATE_LIMIT = "100 per hour"
    API_VERSION = "v1"
    
    # Business logic configuration
    MIN_DELIVERY_DAYS = 7  # Minimum days for delivery
    MAX_DELIVERY_DAYS = 90  # Maximum days for delivery
    DEFAULT_SHIPPING_COST = 10.00  # Default minimum shipping cost
    
    # Cache configuration
    CACHE_TYPE = 'simple'  # Can be 'redis', 'memcached', etc.
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Internationalization
    LANGUAGES = ['en', 'si', 'ta']  # English, Sinhala, Tamil
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Colombo'
    
    # Application features
    FEATURES = {
        'enable_registration': True,
        'enable_email_notifications': True,
        'enable_sms_notifications': False,
        'enable_audit_logging': True,
        'enable_performance_monitoring': True,
        'enable_real_time_tracking': True,
        'enable_advanced_reporting': True
    }
    
    # Third-party service configuration
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    SMS_API_URL = os.environ.get('SMS_API_URL')
    GPS_TRACKING_API_KEY = os.environ.get('GPS_TRACKING_API_KEY')
    PAYMENT_GATEWAY_KEY = os.environ.get('PAYMENT_GATEWAY_KEY')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create upload folder if it doesn't exist
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder and not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Create logs folder if it doesn't exist
        log_file = app.config.get('LOG_FILE')
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Less restrictive security in development
    WTF_CSRF_ENABLED = False  # Disable CSRF in dev for easier testing
    SESSION_COOKIE_SECURE = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'
    
    # Shorter session timeout for development
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    
    # Development database (can be separate)
    DB_NAME = os.environ.get('DEV_DB_NAME', 'supply_chain_dev')
    
    # Enable all features in development
    FEATURES = {
        'enable_registration': True,
        'enable_email_notifications': False,  # Disable to avoid spam in dev
        'enable_sms_notifications': False,
        'enable_audit_logging': True,
        'enable_performance_monitoring': True,
        'enable_real_time_tracking': True,
        'enable_advanced_reporting': True
    }

class TestingConfig(Config):
    """Testing configuration"""
    
    TESTING = True
    DEBUG = False
    
    # Use in-memory database for testing
    DB_NAME = os.environ.get('TEST_DB_NAME', 'supply_chain_test')
    
    # Disable external services during testing
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    
    # Fast sessions for testing
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Disable features that might interfere with testing
    FEATURES = {
        'enable_registration': True,
        'enable_email_notifications': False,
        'enable_sms_notifications': False,
        'enable_audit_logging': False,
        'enable_performance_monitoring': False,
        'enable_real_time_tracking': False,
        'enable_advanced_reporting': True
    }

class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_SSL_STRICT = True
    
    # Shorter session timeout for security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production rate limiting
    API_RATE_LIMIT = "50 per hour"
    
    # Enable all features in production
    FEATURES = {
        'enable_registration': True,
        'enable_email_notifications': True,
        'enable_sms_notifications': True,
        'enable_audit_logging': True,
        'enable_performance_monitoring': True,
        'enable_real_time_tracking': True,
        'enable_advanced_reporting': True
    }
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

class DockerConfig(ProductionConfig):
    """Docker container configuration"""
    
    # Override with container-specific settings
    DB_HOST = os.environ.get('DB_HOST', 'db')  # Docker service name
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')  # Docker service name
    
    # Use environment variables for all sensitive data
    @classmethod
    def init_app(cls, app):
        """Docker-specific initialization"""
        ProductionConfig.init_app(app)
        
        # Additional Docker-specific setup
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s'
        )

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Business logic constants
class BusinessRules:
    """Business rules and constants"""
    
    # Customer types and their discount rates
    CUSTOMER_TYPES = {
        'end': {'discount_rate': 0.00, 'min_order_qty': 1, 'description': 'End consumer'},
        'retail': {'discount_rate': 5.00, 'min_order_qty': 10, 'description': 'Retail customer'},
        'wholesale': {'discount_rate': 15.00, 'min_order_qty': 50, 'description': 'Wholesale customer'}
    }
    
    # Order status workflow
    ORDER_STATUS_FLOW = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['assigned_train', 'cancelled'],
        'assigned_train': ['in_transit_rail', 'cancelled'],
        'in_transit_rail': ['at_warehouse', 'cancelled'],
        'at_warehouse': ['assigned_truck', 'cancelled'],
        'assigned_truck': ['out_for_delivery', 'cancelled'],
        'out_for_delivery': ['delivered', 'returned'],
        'delivered': [],
        'cancelled': [],
        'returned': []
    }
    
    # Transportation capacity limits
    CAPACITY_LIMITS = {
        'train': {'max_weight': 50.0, 'max_volume': 150.0, 'max_items': 1000},
        'truck': {'max_weight': 5.0, 'max_volume': 30.0, 'max_items': 200}
    }
    
    # Working hour limits
    WORKING_HOURS = {
        'driver': {'max_weekly': 40, 'max_daily': 8},
        'driver_assistant': {'max_weekly': 60, 'max_daily': 10}
    }
    
    # Shipping cost factors
    SHIPPING_FACTORS = {
        'weight_factor': 1.5,  # Cost per kg
        'volume_factor': 2.0,  # Cost per cubic meter
        'distance_factor': 0.5,  # Cost per km
        'route_type_multipliers': {
            'local': 1.0,
            'regional': 1.2,
            'express': 1.5
        }
    }
    
    # Report configurations
    REPORT_CONFIGS = {
        'sales_report': {
            'default_period': 30,  # days
            'max_period': 365,  # days
            'formats': ['html', 'pdf', 'excel']
        },
        'inventory_report': {
            'low_stock_threshold': 10,
            'out_of_stock_alert': True,
            'formats': ['html', 'pdf', 'excel']
        },
        'transport_report': {
            'default_period': 7,  # days
            'utilization_threshold': 80,  # percentage
            'formats': ['html', 'pdf']
        }
    }

# Utility functions for configuration
def is_feature_enabled(feature_name):
    """Check if a feature is enabled"""
    config_class = get_config()
    return config_class.FEATURES.get(feature_name, False)

def get_business_rule(rule_name):
    """Get a business rule value"""
    return getattr(BusinessRules, rule_name, None)

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    config_class = get_config()
    
    # Check required environment variables
    required_vars = ['SECRET_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD']
    for var in required_vars:
        if not getattr(config_class, var, None):
            errors.append(f"Missing required configuration: {var}")
    
    # Check database connection parameters
    if not config_class.DB_NAME:
        errors.append("Database name not configured")
    
    # Check upload folder
    if not os.path.exists(config_class.UPLOAD_FOLDER):
        try:
            os.makedirs(config_class.UPLOAD_FOLDER)
        except Exception as e:
            errors.append(f"Cannot create upload folder: {e}")
    
    return errors

if __name__ == '__main__':
    # Configuration validation
    print("🔧 Validating configuration...")
    
    errors = validate_config()
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid")
    
    # Display current configuration
    config_class = get_config()
    print(f"\n📋 Current environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"📊 Database: {config_class.DB_HOST}:{config_class.DB_PORT}/{config_class.DB_NAME}")
    print(f"🔒 Debug mode: {getattr(config_class, 'DEBUG', False)}")
    print(f"⏰ Session timeout: {config_class.PERMANENT_SESSION_LIFETIME}")
    
    # Display enabled features
    print("\n🚀 Enabled features:")
    for feature, enabled in config_class.FEATURES.items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature}")