import json
import secrets
from datetime import datetime, timezone, timedelta
from hashlib import md5
from time import time
from typing import Optional

import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from celery import shared_task
from flask import current_app as app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login
from app.models import timestamp
from app.models.message import Message
from app.models.notification import Notification
from app.models.post import Post
from app.models.task import Task
from app.models.mixins import PaginatedAPIMixin

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)


class User(PaginatedAPIMixin, UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[timestamp]

    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    membership: so.WriteOnlyMapped['Membership'] = so.relationship(back_populates='user')
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers'
    )
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following'
    )

    last_message_read_time: so.Mapped[datetime | None]

    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.sender_id', back_populates='author'
    )
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(
        foreign_keys='Message.recipient_id', back_populates='recipient'
    )
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user')
    tasks: so.WriteOnlyMapped['Task'] = so.relationship(back_populates='user')

    token: so.Mapped[str | None] = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[datetime | None]

    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).filter_by(token=token))
        if user is None or user.token_expiration.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        author_alias = so.aliased(User)
        follower_alias = so.aliased(User)
        query = (sa.select(Post)
                 .join(Post.author.of_type(author_alias))
                 .join(author_alias.followers.of_type(follower_alias), isouter=True)
                 .where(sa.or_(follower_alias.id == self.id, author_alias.id == self.id))
                 .group_by(Post)
                 .order_by(Post.timestamp.desc()))
        return query

    def unread_message_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        query = sa.select(Message).where(Message.recipient == self, Message.timestamp > last_read_time)
        return db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))

    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().filter_by(name=name))
        notification = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(notification)
        return notification

    def launch_task(self, task: shared_task, description, *args, **kwargs):
        job = task.apply_async(args=[self.id, *args], kwargs={**kwargs}, countdown=5)
        task = Task(id=job.id, name=task.name, description=description, user=self)
        self.add_notification('task_progress', {'task_id': job.id, 'progress': 0})
        db.session.add(task)
        db.session.commit()
        return task

    def get_tasks_in_progress(self):
        query = self.tasks.select().filter_by(complete=False)
        return db.session.scalars(query)

    def get_task_in_progress(self, name):
        query = self.tasks.select().filter_by(name=name, complete=False)
        return db.session.scalar(query)

    def posts_count(self):
        query = sa.select(sa.func.count()).select_from(self.posts.select().subquery())
        return db.session.scalar(query)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.replace(tzinfo=timezone.utc).isoformat() if self.last_seen else None,
            'about_me': self.about_me,
            'post_count': self.posts_count(),
            'follower_count': self.followers_count(),
            'following_count': self.following_count(),
            '_links': {
                'self': url_for('api.get_user', user_id=self.id),
                'followers': url_for('api.get_followers', user_id=self.id),
                'following': url_for('api.get_following', user_id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ('username', 'email', 'about_me'):
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def __repr__(self):
        return f'<User {self.username}>'


@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
