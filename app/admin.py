from sqladmin import Admin, ModelView
from sqladmin.application import Admin as AdminApp

from app.database import engine
from app.models import User, CitizenRequest, RequestType, Proof
from app.models.user import UserRole, UserSource
from app.models.request import RequestStatus
from app.models.proof import ProofStatus


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_list = [User.id, User.telegram_id, User.username, User.role, User.source, User.created_at]
    column_searchable_list = [User.username]
    column_sortable_list = [User.id, User.created_at]
    form_columns = [User.telegram_id, User.username, User.password_hash, User.role, User.source]


class CitizenRequestAdmin(ModelView, model=CitizenRequest):
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-file-lines"
    column_list = [
        CitizenRequest.id,
        CitizenRequest.user_id,
        CitizenRequest.status,
        CitizenRequest.assigned_operator_id,
        CitizenRequest.assigned_executor_id,
        CitizenRequest.title,
        CitizenRequest.created_at,
    ]
    column_searchable_list = [CitizenRequest.title, CitizenRequest.description]
    column_sortable_list = [CitizenRequest.id, CitizenRequest.created_at, CitizenRequest.updated_at]
    form_columns = [
        CitizenRequest.user_id,
        CitizenRequest.type_id,
        CitizenRequest.status,
        CitizenRequest.assigned_operator_id,
        CitizenRequest.assigned_executor_id,
        CitizenRequest.title,
        CitizenRequest.description,
        CitizenRequest.address,
        CitizenRequest.rating,
        CitizenRequest.citizen_confirmed,
        CitizenRequest.citizen_review,
    ]


class RequestTypeAdmin(ModelView, model=RequestType):
    name = "Тип заявки"
    name_plural = "Типы заявок"
    icon = "fa-solid fa-tag"
    column_list = [RequestType.id, RequestType.name, RequestType.slug]
    column_searchable_list = [RequestType.name, RequestType.slug]
    form_columns = [RequestType.name, RequestType.slug]


class ProofAdmin(ModelView, model=Proof):
    name = "Пруф"
    name_plural = "Пруфы"
    icon = "fa-solid fa-image"
    column_list = [Proof.id, Proof.request_id, Proof.executor_id, Proof.operator_id, Proof.status, Proof.created_at]
    column_sortable_list = [Proof.id, Proof.created_at]
    form_columns = [Proof.request_id, Proof.executor_id, Proof.operator_id, Proof.file_ref, Proof.comment, Proof.status]


def setup_admin(app) -> AdminApp:
    admin = Admin(app, engine, base_url="/admin", title="Платформа помощи гражданам")
    admin.add_view(UserAdmin)
    admin.add_view(CitizenRequestAdmin)
    admin.add_view(RequestTypeAdmin)
    admin.add_view(ProofAdmin)
    return admin
