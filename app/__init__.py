from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Пожалуйста, авторизуйтесь'
# handler = RotatingFileHandler()
handler = RotatingFileHandler('microblog.log')
handler.setLevel(logging.INFO)
# logger = logging.getLogger(__name__)
# logging.basicConfig(filename='myapp.log', level=logging.ERROR)
app.logger.addHandler(handler)


from app import routes, models
