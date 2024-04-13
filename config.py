import hashlib
from os import environ, path
basedir = path.abspath(path.dirname(__file__))


class Config:
    SECRET_KEY = environ.get('SECRET_KEY') or 'secret'
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL') or 'sqlite:///' + path.join(basedir, 'app.db')


class Development(Config):
    API_KEY = environ.get('API_KEY') or 'api'


class Production(Config):
    SECRET_KEY = hashlib.md5((environ.get('SECRET_KEY') or 'SECRET').encode()).hexdigest()
    API_KEY = hashlib.md5((environ.get('API_KEY') or 'API').encode()).hexdigest()
