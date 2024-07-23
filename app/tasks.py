import json
import sys
import time
from celery import shared_task
from app import db
from app.models.task import Task
from app.models.user import User
from app.models.post import Post
from flask_mail import Message
from app import mail
from flask import current_app as app, render_template
import sqlalchemy as sa
from app.email import send_email


def _set_task_progress(job, progress):
    job.update_state(
        state='PROGRESS',
        meta={
            'progress': progress
        }
    )
    task = db.session.get(Task, job.request.id)
    task.user.add_notification('task_progress', {'task_id': job.request.id, 'progress': progress})
    if progress >= 100:
        job.update_state(
            state='SUCCESS',
        )
        task.complete = True
    db.session.commit()


@shared_task(max_retries=3)
def send_email(subject, sender, recipients, text_body, html_body, attachments=None):
    msg = Message(subject, recipients, text_body, html_body, sender=sender)
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    mail.send(msg)


@shared_task(bind=True, max_retries=3)
def export_posts_task(self, user_id):
    user = db.session.get(User, user_id)
    try:
        data = []
        i = 0
        total_posts = db.session.scalar(sa.select(sa.func.count()).select_from(
            user.posts.select().subquery()
        ))
        for post in db.session.scalars(user.posts.select().order_by(
                Post.timestamp.asc()
        )):
            data.append({'body': post.body, 'timestamp': post.timestamp.isoformat() + 'Z'})
            time.sleep(3)
            i += 1
            progress = 100 * i // total_posts
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress
                }
            )
            task = db.session.get(Task, self.request.id)
            task.user.add_notification('task_progress', {'task_id': self.request.id, 'progress': progress})
            db.session.commit()
            # _set_task_progress(self, 100 * i // total_posts)
        send_email(
            'Экспорт постов',
            sender=app.config['ADMINS'][0], recipients=[user.email],
            text_body=render_template('email/export_posts.txt', user=user),
            html_body=render_template('email/export_posts.html', user=user),
            attachments=[('posts.json', 'application/json', json.dumps({'posts': data}, indent=4))]
        )
    except Exception as e:
        app.logger.error(f"Exception: ${e}, ${e.args}", exc_info=sys.exc_info())
        # _set_task_progress(self, 100)
        self.update_state(
            state='FAILURE',
            meta={
                'progress': 100
            }
        )
    finally:
        # _set_task_progress(self, 100)
        task = db.session.get(Task, self.request.id)
        task.user.add_notification('task_progress', {'task_id': self.request.id, 'progress': 100})
        task.complete = True
        db.session.commit()
