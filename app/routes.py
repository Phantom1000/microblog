from app import app
from flask import request, render_template, flash, redirect, url_for
from app.forms import LoginForm

@app.route('/')
@app.route('/index')
def index():
    api_key = app.config.get("API_KEY")
    app.logger.info(f'{request.method} request to {request.path}')
    user = {'username': 'Phantom'}
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
    return render_template('index.html', title='Главная', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Вы успешно вошли, имя пользователя - {form.username.data}, запомнить - {form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Войти', form=form)