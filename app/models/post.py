import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from typing import Optional
from app.models import intpk, timestamp
from app.models.mixins import SearchableMixin


class Post(db.Model, SearchableMixin):
    __searchable__ = ['body']
    id: so.Mapped[intpk]
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[timestamp]
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    author: so.Mapped['User'] = so.relationship(back_populates='posts')
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))

    def __repr__(self):
        return f'<Post {self.body}>'
