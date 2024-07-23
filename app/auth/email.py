from flask import render_template, current_app
from app.tasks import send_email


def send_password_reset_email(user):
    token = user.get_password_token()
    subject: str = "Сброс пароля"
    # send_email(
    #     subject,
    #     sender=current_app.config['ADMINS'][0],
    #     recipients=[user.email],
    #     text_body=render_template('email/reset_password.txt', user=user, token=token),
    #     html_body=render_template('email/reset_password.html', user=user, token=token)
    # )
    send_email.delay(
        subject,
        current_app.config['ADMINS'][0],
        [user.email],
        render_template('email/reset_password.txt', user=user, token=token),
        render_template('email/reset_password.html', user=user, token=token)
    )
