import os

class Config:
    # Secret key for CSRF protection and session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or '23cfd7f3ef8eabcc3d02b01250315bd329e19942f0d51b8a264943b516114543'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///marketplace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False