from app import create_app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models.user import User
from app.models.post import Post

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}


if __name__ == '__main__':
    # app.run(ssl_context=('cert.pem', 'key.pem'))
    app.run()
