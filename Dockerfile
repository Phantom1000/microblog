FROM python:slim

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql cryptography

COPY boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP microblog.py
