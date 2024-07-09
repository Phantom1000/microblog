import logging
import os
from logging.handlers import RotatingFileHandler, SMTPHandler

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['develop.nikita@yandex.ru']
    TRANSLATOR_KEY = os.environ.get('TRANSLATOR_KEY')
    # CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    # CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
    CELERY = dict(
        broker_url="redis://localhost",
        result_backend="redis://localhost",
        task_ignore_result=True,
    ),
    POSTS_PER_PAGE = 5
    LANGUAGES = ['ru', 'en']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    @staticmethod
    def init_app(app):
        pass


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_ECHO = True

    @classmethod
    def init_app(cls, app):
        BaseConfig.init_app(app)
        if not app.debug:
            if cls.MAIL_SERVER:
                auth = None
                if cls.MAIL_USERNAME or cls.MAIL_PASSWORD:
                    auth = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
                secure = None
                if cls.MAIL_USE_TLS:
                    secure = ()
                mail_handler = SMTPHandler(
                    mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                    # fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                    fromaddr=cls.MAIL_USERNAME,
                    toaddrs=cls.ADMINS, subject='Ошибки в блоге',
                    credentials=auth, secure=secure
                )
                mail_handler.setLevel(logging.ERROR)
                app.logger.addHandler(mail_handler)

            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Блог запущен')


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "test": TestConfig,
    "default": ProductionConfig,
}
