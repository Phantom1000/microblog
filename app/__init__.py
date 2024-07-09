from flask import Flask, request, current_app
from config import ProductionConfig, config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
import os
from elasticsearch import Elasticsearch
from celery import Celery, Task


def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


def celery_init_app(app: Flask) -> Celery:
    # class FlaskTask(Task):
    #     def __call__(self, *args: object, **kwargs: object) -> object:
    #         with app.app_context():
    #             return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Пожалуйста, авторизуйтесь'
mail = Mail()
moment = Moment()
babel = Babel()
config_name = os.getenv('CONFIG') or 'production'


def create_app(config_class=config[config_name]) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    app.elasticsearch = Elasticsearch(app.config['ELASTICSEARCH_URL']) if app.config['ELASTICSEARCH_URL'] else None
    # app.celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    # app.celery.conf.update(app.config)
    # app.config.from_prefixed_env()
    # app.config.from_mapping(
    #     CELERY=dict(
    #         broker_url="redis://localhost:6379/0",
    #         result_backend="redis://localhost:6379/0",
    #         task_ignore_result=True,
    #     ),
    # )
    # app.config.from_prefixed_env()
    celery_init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.main.group import GroupAPI, GroupsAPI, MembersAPI
    app.add_url_rule("/groups/<int:group_id>", view_func=GroupAPI.as_view("group"))
    app.add_url_rule("/groups", view_func=GroupsAPI.as_view("groups"))
    app.add_url_rule("/members", view_func=MembersAPI.as_view("members"))

    return app
    # logger = logging.getLogger(__name__)
    # logging.basicConfig(filename='myapp.log', level=logging.ERROR)
    # if not app.debug and not app.testing:
    #     if app.config['MAIL_SERVER']:
    #         auth = None
    #         if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
    #             auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    #         secure = None
    #         if app.config['MAIL_USE_TLS']:
    #             secure = ()
    #         mail_handler = SMTPHandler(
    #             mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
    #             # fromaddr='no-reply@' + app.config['MAIL_SERVER'],
    #             fromaddr=app.config['MAIL_USERNAME'],
    #             toaddrs=app.config['ADMINS'], subject='Ошибки в блоге',
    #             credentials=auth, secure=secure
    #         )
    #         mail_handler.setLevel(logging.ERROR)
    #         app.logger.addHandler(mail_handler)
    #
    #     if not os.path.exists('logs'):
    #         os.mkdir('logs')
    #     file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
    #     file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    #     file_handler.setLevel(logging.INFO)
    #     app.logger.addHandler(file_handler)
    #     app.logger.setLevel(logging.INFO)
    #     app.logger.info('Блог запущен')


from app.models import mixins
