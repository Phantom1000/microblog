from celery.result import AsyncResult

from app import db
from flask import request, render_template, flash, redirect, url_for, g, current_app as app
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm

from flask_login import current_user, login_required
import sqlalchemy as sa
from app.models.user import User
from app.models.post import Post
from app.models.message import Message
from app.models.notification import Notification

from datetime import datetime, timezone
from langdetect import detect, LangDetectException
from app.translate import translate
from flask_babel import get_locale
from app.main import bp
import sqlalchemy.orm as so
from celery import shared_task
from app.tasks import export_posts_task


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    api_key = app.config.get("API_KEY")
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash('Запись успешно опубликована')
        return redirect(url_for('main.index'))
    app.logger.info(f'{request.method} request to {request.path}')
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Главная', posts=posts.items,
                           form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).options(so.selectinload(Post.author)).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Все записи', posts=posts,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username: str):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           title=user.username, form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/edit/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Изменения успешно сохранены')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title="Редактирование профиля", form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).filter_by(username=username)
        )
        if user is None:
            flash(f'Пользователь {username} не найден')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Невозможно подписаться на самого себя')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'Вы успешно подписались на {username}')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).filter_by(username=username)
        )
        if user is None:
            flash(f'Пользователь {username} не найден')
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('Невозможно отписаться от самого себя')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'Вы успешно отписались от {username}')
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    data = request.get_json()
    return {'text': translate(data['text'], data['source_language'], data['dest_language'])}


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) if total > page * app.config[
        'POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) if page > 1 else None
    return render_template('search.html', title='Поиск', posts=posts, next_url=next_url, prev_url=prev_url)


@bp.route("/user/<username>/popup")
@login_required
def user_popup(username: str):
    user = db.first_or_404(sa.select(User).filter_by(username=username))
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/send_message/<recipient>', methods=('GET', 'POST'))
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).filter_by(username=recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.unread_message_count())
        db.session.commit()
        flash('Сообщение отправлено')
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title='Отправить сообщение', form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(Message.timestamp.desc())
    messages = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(Notification.timestamp > since).order_by(
        Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': notification.name,
        'data': notification.get_data(),
        'timestamp': notification.timestamp
    } for notification in notifications]


@bp.get("/export_posts")
@login_required
def export_posts():
    if current_user.get_task_in_progress('app.tasks.export_posts_task'):
        flash('Экспорт постов уже запущен')
    else:
        task = current_user.launch_task(export_posts_task, "Экспорт постов...")
        return redirect(url_for('main.user', username=current_user.username, task_id=task.id))
    return redirect(url_for('main.user', username=current_user.username))


@bp.route("/task_status/<task_id>")
def task_status(task_id):
    task = AsyncResult(task_id)
    response = {
        "ready": task.ready(),
        "successful": task.successful(),
        "progress": 0
    }
    if task.status == 'PROGRESS' or task.status == 'SUCCESS':
        response['progress'] = task.info.get("progress"),
    return response
