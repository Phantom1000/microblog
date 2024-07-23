import sqlalchemy as sa
import sqlalchemy.orm as so

from app import db
from app.models import intpk, timestamp


class Message(db.Model):
    id: so.Mapped[intpk]
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[timestamp]

    author: so.Mapped['User'] = so.relationship(
        foreign_keys='Message.sender_id',
        back_populates='messages_sent'
    )

    recipient: so.Mapped['User'] = so.relationship(
        foreign_keys='Message.recipient_id',
        back_populates='messages_received'
    )

    def __repr__(self):
        return f'<Message {self.body}>'
