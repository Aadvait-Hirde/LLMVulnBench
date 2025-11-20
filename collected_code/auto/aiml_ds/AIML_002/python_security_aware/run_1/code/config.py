import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 1024 * 1024))
    MODEL_PATH = os.getenv('MODEL_PATH', 'model.pkl')
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 100))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
