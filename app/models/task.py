import sqlalchemy as sa
import sqlalchemy.orm as so
from celery.result import AsyncResult

from app import db
from app.models import timestamp


class Task(db.Model):
    id: so.Mapped[str] = so.mapped_column(sa.String(36), primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(128))
    timestamp: so.Mapped[timestamp]
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'))
    user: so.Mapped['User'] = so.relationship(back_populates='tasks')
    complete: so.Mapped[bool] = so.mapped_column(default=False)

    def get_result(self) -> AsyncResult:
        return AsyncResult(self.id)

    def get_progress(self):
        job = self.get_result()
        if job:
            if job.state == 'PENDING':
                return 0
            if job.state == 'FAILURE':
                return 100
            return job.info.get('progress', 0)
        return 100
