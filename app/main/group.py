from flask.views import MethodView
from flask import request, url_for, abort, jsonify
from app.models.group import Group, Membership, Role
from app.models.user import User
from app import db
import sqlalchemy as sa
import sqlalchemy.orm as so


class GroupAPI(MethodView):
    init_every_request = False

    def get(self, group_id):
        group: Group = db.get_or_404(Group, group_id)
        return {"item": group.to_json()}

    def put(self, group_id):
        name: str = request.json.get("name")
        if name:
            group: Group = db.get_or_404(Group, group_id)
            group.name = name
            db.session.commit()
            return {"message": "Изменения сохранены", "item": group.to_json()}
        else:
            abort(422, "Введите имя")

    def delete(self, group_id):
        group: Group = db.get_or_404(Group, group_id)
        db.session.delete(group)
        db.session.commit()
        return {"message": "Группа успешно удалена"}


class GroupsAPI(MethodView):
    init_every_request = False

    def get(self):
        groups: list[Group] = db.session.scalars(sa.select(Group)).all()
        return {"items": [group.to_json() for group in groups]}

    def post(self):
        name: str = request.json.get("name")
        if name:
            group: Group = Group(name=name)
            db.session.add(group)
            db.session.commit()
            return {"message": "Группа успешно создана", "item": group.to_json()}
        else:
            abort(422, "Введите имя")


class MembersAPI(MethodView):
    init_every_request = False

    def get(self):
        group_id = request.json.get("group")
        group: Group = db.get_or_404(Group, group_id)
        query = group.membership.select().options(so.joinedload(Membership.user).load_only(User.username))
        count_query = sa.select(Membership.role, Group.name, sa.func.count().label("role_count")).select_from(
            Membership).join(
            Membership.group).filter(
            Membership.role != Role.MEMBER).group_by(Group.name).group_by(Membership.role).having(sa.func.count() > 0)
        members = db.session.scalars(query).all()
        result = db.session.execute(count_query).all()
        groups = set(map(lambda item: item[1], result))
        query_1 = group.membership.select().join(Membership.user).filter(User.id == 1).options(
            so.contains_eager(Membership.user))
        count = [{
            "group": group,
            "data": [{
                "role": item[0].value,
                "count": item.role_count,
            } for item in result if item[1] == group]
        } for group in groups]
        result_1 = db.session.scalars(query_1).all()
        return {
            "count": count,
            "items": [{"id": member.user_id, "username": member.user.username, "role": member.role.value} for member in
                      members]}

    def post(self):
        group_id = request.json.get("group")
        user_id = request.json.get("user")
        if group_id and user_id:
            group: Group = db.get_or_404(Group, group_id)
            user: User = db.get_or_404(User, user_id)
            is_member = db.session.get(Membership, (user.id, group.id))
            if not is_member:
                membership: Membership = Membership()
                membership.user = user
                membership.group = group
                db.session.add(membership)
                db.session.commit()
                return {"message": "Пользователь добавлен в группу"}
            else:
                return {"message": "Пользователь уже добавлен в группу"}
        else:
            abort(422, "Введите пользователя и группу")

    def put(self):
        group_id = request.json.get("group")
        user_id = request.json.get("user")
        if group_id and user_id:
            group: Group = db.get_or_404(Group, group_id)
            user: User = db.get_or_404(User, user_id)
            member = db.session.get(Membership, (user.id, group.id))
            if member:
                role = Role[request.json.get("role")]
                member.role = role
                db.session.commit()
                return {"message": "Пользователь добавлен в группу"}
            else:
                return {"message": "Пользователя нет в группе"}
        else:
            abort(422, "Введите пользователя и группу")

    def delete(self):
        group_id = request.json.get("group")
        user_id = request.json.get("user")
        if group_id and user_id:
            group: Group = db.get_or_404(Group, group_id)
            user: User = db.get_or_404(User, user_id)
            member = db.session.get(Membership, (user.id, group.id))
            if member:
                db.session.delete(member)
                db.session.commit()
                return {"message": "Пользователь удален из группы"}
            else:
                return {"message": "Пользователя нет в группе"}
        else:
            abort(422, "Введите пользователя и группу")
