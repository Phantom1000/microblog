from app import db, create_app
from config import DevelopmentConfig
from typing import Annotated
import sqlalchemy.orm as so
from datetime import datetime, timezone


intpk = Annotated[int, so.mapped_column(primary_key=True)]
timestamp = Annotated[datetime, so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))]


if __name__ == "__main__":
    app = create_app(DevelopmentConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
