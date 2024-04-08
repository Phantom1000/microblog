from flask import Flask
from config import Config
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)
# handler = RotatingFileHandler()
handler = RotatingFileHandler('microblog.log')
handler.setLevel(logging.INFO)
# logger = logging.getLogger(__name__)
# logging.basicConfig(filename='myapp.log', level=logging.ERROR)
app.logger.addHandler(handler)


from app import routes