from app import app, db
from flask import request, render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User
from urllib.parse import urlsplit


@app.route('/')
@app.route('/index')
@login_required
def index():
    api_key = app.config.get("API_KEY")
    app.logger.info(f'{request.method} request to {request.path}')
    posts = [
        {
            'author': {'username': 'Ivan'},
            'body': 'Какой прекрасный день!'
        },
        {
            'author': {'username': 'Petr'},
            'body': 'Всем привет'
        },
    ]
    return render_template('index.html', title='Главная', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user: User = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Проверьте имя пользователя или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        flash(f'Вы успешно вошли')
        return redirect(next_page)
    return render_template('login.html', title='Войти', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Вы успешно зарегистрировались')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)
