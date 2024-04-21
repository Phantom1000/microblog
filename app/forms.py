from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(message='Введите имя пользователя')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Введите пароль')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(message='Введите имя пользователя')])
    email = StringField('Email', validators=[DataRequired(message='Введите email'), Email(message='Проверьте email')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Введите пароль')])
    password_confirm = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Пользователь с таким именем уже существует')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Пользователь с таким email уже существует')
