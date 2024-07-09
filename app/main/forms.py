from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
import sqlalchemy as sa
from app import db
from app.models.user import User
from flask import request


class EditProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    about_me = TextAreaField('Обо мне', validators=[Length(min=0, max=140)])
    submit = SubmitField('Сохранить')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError('Пользователь с таким именем уже существует')


class EmptyForm(FlaskForm):
    submit = SubmitField('Отправить')


class PostForm(FlaskForm):
    post = TextAreaField('Что у Вас нового?', validators=[
        DataRequired(), Length(min=1, max=140)
    ])
    submit = SubmitField('Отправить')


class SearchForm(FlaskForm):
    q = StringField('Найти...', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)
