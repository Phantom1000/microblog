from flask_mail import Message
from app import mail
from flask import current_app as app
from threading import Thread
from celery import shared_task


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, recipients, text_body, html_body, sender=sender)
    Thread(target=send_async_email, args=(app._get_current_object(), msg)).start()


@shared_task(ignore_result=False)
def send_celery_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, recipients, text_body, html_body, sender=sender)
    mail.send(msg)
