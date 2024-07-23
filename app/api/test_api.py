import datetime

import pytest
import sqlalchemy as sa

from app import create_app
from app import db
from app.models.user import User
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        test_user = User(username="test", email="test@example.com")
        test_user2 = User(username="test2", email="test2@example.com")
        test_user.set_password('test')
        test_user2.set_password('test')
        db.session.add_all([test_user, test_user2])
        test_user2.following.add(test_user)
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post('/api/tokens', auth=(username, password))

    def logout(self, token):
        return self._client.delete('/api/tokens', headers={"Authorization": f"Bearer {token}"})


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.mark.parametrize(('username', 'password', 'email', 'message'), (
        ('', '12345', 'ivan@example.com', 'Введите имя пользователя'),
        ('ivan', '12345', '', 'Введите email'),
        ('ivan', '', 'ivan@example.com', 'Введите пароль'),
        ('test', '12345', 'test@example.com', 'Пользователь с таким именем уже существует'),
        ('ivan', '12345', 'test@example.com', 'Пользователь с таким email уже существует'),
))
def test_validate_register(client, username, password, email, message):
    response = client.post('/api/users', json={
        'username': username, 'password': password, 'email': email, 'about_me': 'I am Ivan'
    })
    assert response.status_code == 400
    assert message in response.json['message']


def test_register(app, client):
    response = client.post('/api/users', json={
        'username': 'ivan', 'password': '12345', 'email': 'ivan@example.com', 'about_me': 'I am Ivan'
    })
    assert 'ivan' in response.json['username']
    assert response.status_code == 201
    assert response.headers["Location"] == "/api/users/3"
    with app.app_context():
        assert db.session.scalar(sa.select(User).filter_by(username='ivan'))


@pytest.mark.parametrize(('username', 'password'), (
        ('', '12345'),
        ('ivan', ''),
        ('ivan', '12345'),
))
def test_validate_login(client, username, password):
    response = client.post('/api/tokens', auth=(username, password))
    assert response.status_code == 401


def test_login(client):
    response = client.post('/api/tokens', auth=('test', 'test'))
    assert response.json['token']
    assert response.status_code == 200


def test_get_user(auth, client):
    token = auth.login().json['token']
    response = client.get('/api/users/1', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json['username'] == 'test'


def test_get_users(auth, client):
    token = auth.login().json['token']
    response = client.get('/api/users', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json["items"]) == 2
    assert response.json["items"][0]['username'] == 'test'


def test_update_user(app, auth, client):
    token = auth.login().json['token']
    response = client.put('/api/users/1', json={'about_me': 'Test app'}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json['about_me'] == 'Test app'
    with app.app_context():
        assert db.session.get(User, 1).about_me == 'Test app'


def test_get_following(auth, client):
    token = auth.login().json['token']
    response = client.get('/api/users/2/following', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]['username'] == 'test'


def test_get_followers(auth, client):
    token = auth.login().json['token']
    response = client.get('/api/users/1/followers', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]['username'] == 'test2'


def test_logout(app, auth, client):
    token = auth.login().json['token']
    response = client.delete('/api/tokens', headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    with app.app_context():
        assert db.session.get(User, 1).token_expiration.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(
            datetime.timezone.utc)
