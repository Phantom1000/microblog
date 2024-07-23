from time import time
import json
import sqlalchemy as sa
import sqlalchemy.orm as so

from app import db
from app.models import intpk


class Notification(db.Model):
    id: so.Mapped[intpk]
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    timestamp: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

    user: so.Mapped['User'] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))
