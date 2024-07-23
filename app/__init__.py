from flask import Flask, request, current_app
from config import get_config_class
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
from elasticsearch import Elasticsearch
from celery import Celery, Task
import os


def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
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


def create_app(config_class=get_config_class()) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.from_mapping(
        CELERY={
            "broker_url": app.config["REDIS_URL"],
            "result_backend": app.config["REDIS_URL"],
            "task_ignore_result": True,
        },
    )
    config_class.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    app.elasticsearch = Elasticsearch(app.config['ELASTICSEARCH_URL']) if app.config['ELASTICSEARCH_URL'] else None
    celery_init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.main.group import GroupAPI, GroupsAPI, MembersAPI
    app.add_url_rule("/groups/<int:group_id>", view_func=GroupAPI.as_view("group"))
    app.add_url_rule("/groups", view_func=GroupsAPI.as_view("groups"))
    app.add_url_rule("/members", view_func=MembersAPI.as_view("members"))

    return app


from app.models import mixins
