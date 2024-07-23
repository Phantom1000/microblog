from app.api import bp
from app.models.user import User
from app import db
from flask import request, url_for, abort
import sqlalchemy as sa
from app.api.errors import bad_request
from app.api.auth import token_auth


@bp.get('/users/<int:user_id>')
@token_auth.login_required
def get_user(user_id):
    return db.get_or_404(User, user_id).to_dict()


@bp.get('/users')
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(sa.select(User), page, per_page, 'api.get_users')


@bp.get('/users/<int:user_id>/followers')
@token_auth.login_required
def get_followers(user_id):
    user = db.get_or_404(User, user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.followers.select(), page, per_page, 'api.get_followers', user_id=user_id)


@bp.get('/users/<int:user_id>/following')
@token_auth.login_required
def get_following(user_id):
    user = db.get_or_404(User, user_id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_collection_dict(user.following.select(), page, per_page, 'api.get_following', user_id=user_id)


@bp.post('/users')
def create_user():
    data = request.get_json()
    if not data.get('username'):
        return bad_request('Введите имя пользователя')
    if not data.get('email'):
        return bad_request('Введите email')
    if not data.get('password'):
        return bad_request('Введите пароль')
    if db.session.scalar(sa.select(User).filter_by(username=data['username'])):
        return bad_request('Пользователь с таким именем уже существует')
    if db.session.scalar(sa.select(User).filter_by(email=data['email'])):
        return bad_request('Пользователь с таким email уже существует')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201, {'Location': url_for('api.get_user', user_id=user.id)}


@bp.put('/users/<int:user_id>')
@token_auth.login_required
def update_user(user_id):
    if token_auth.current_user().id != user_id:
        abort(403)
    user = db.get_or_404(User, user_id)
    data = request.get_json()
    if 'username' in data and data['username'] != user.username and db.session.scalar(
            sa.select(User).filter_by(username=data['username'])):
        return bad_request('Пользователь с таким именем уже существует')
    if 'email' in data and data['email'] != user.email and db.session.scalar(
            sa.select(User).filter_by(email=data['email'])):
        return bad_request('Пользователь с таким email уже существует')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return user.to_dict()
