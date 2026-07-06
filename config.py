import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-1337')
    
    # Payload limits (Zero-load filtering guards)
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # Strict 25MB limit handled at HTTP layer
    MAX_BATCH_FILES = 4
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Task Broker configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL