from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# handler = RotatingFileHandler()
handler = RotatingFileHandler('microblog.log')
handler.setLevel(logging.INFO)
# logger = logging.getLogger(__name__)
# logging.basicConfig(filename='myapp.log', level=logging.ERROR)
app.logger.addHandler(handler)


from app import routes, models
