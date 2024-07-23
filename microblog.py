from app import create_app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models.user import User
from app.models.post import Post
from app.models.message import Message
from app.models.notification import Notification
from app.models.task import Task

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post,
            'Message': Message, 'Task': Task, }


if __name__ == '__main__':
    # app.run(ssl_context=('cert.pem', 'key.pem'))
    app.run(debug=True)
