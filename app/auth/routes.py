from flask import redirect, url_for, render_template, flash, request
from flask_login import current_user, login_user, logout_user

from app.auth import bp
from app.auth.forms import ResetPasswordForm, ResetPasswordRequestForm, RegistrationForm, LoginForm
from app.auth.email import send_password_reset_email
from app import db
from urllib.parse import urlsplit
import sqlalchemy as sa
from app.models.user import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user: User = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Проверьте имя пользователя или пароль')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.index')
        flash(f'Вы успешно вошли')
        return redirect(next_page)
    return render_template('login.html', title='Войти', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Регистрация', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data)
        )
        if user:
            send_password_reset_email(user)
        flash('Проверьте свою электронную почту для получения инструкцей по сбросу пароля')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html', title='Сброс пароля', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ваш пароль был сброшен')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)
