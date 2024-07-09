import enum

import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models import intpk, timestamp
from app.models.user import User


class Role(enum.Enum):
    ADMIN = 'Администратор'
    MODERATOR = 'Модератор'
    MEMBER = 'Участник'


class Group(db.Model):
    id: so.Mapped[intpk]
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    timestamp: so.Mapped[timestamp]
    membership: so.WriteOnlyMapped['Membership'] = so.relationship(back_populates='group', passive_deletes=True)

    def __repr__(self):
        return f'<Group {self.name}>'

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            # "members": db.session.scalars(self.membership.select()).all()
        }


class Membership(db.Model):
    role: so.Mapped[Role] = so.mapped_column(default=Role.MEMBER)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id', ondelete='cascade'), primary_key=True,
                                               index=True)
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('group.id', ondelete='cascade'), primary_key=True,
                                                index=True)
    user: so.Mapped['User'] = so.relationship(back_populates='membership')
    group: so.Mapped['Group'] = so.relationship(back_populates='membership')
