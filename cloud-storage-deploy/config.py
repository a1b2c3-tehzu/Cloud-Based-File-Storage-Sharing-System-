import os

class Config:
    # Database Configuration
    # Using SQLite for testing (change to MySQL when available)
    DB_TYPE = "sqlite"
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "cloud_storage_db"
    SQLITE_DB = "cloud_storage.db"
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = 'your_actual_aws_access_key'
    AWS_SECRET_ACCESS_KEY = 'your_actual_aws_secret_key'
    AWS_REGION = 'us-east-1'
    S3_BUCKET_NAME = 'your-unique-bucket-name'

    
    # Flask Configuration
    SECRET_KEY = 'your_secret_key_here_change_in_production'
    UPLOAD_FOLDER = 'static/temp_uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'cloud_storage_'
    
    # Security Configuration
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
    
    # Share Link Configuration
    DEFAULT_SHARE_EXPIRY_HOURS = 24
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    
    # Override with production values
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
