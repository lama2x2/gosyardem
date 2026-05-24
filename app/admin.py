from sqladmin import Admin, ModelView
from sqladmin.application import Admin as AdminApp

from app.admin_auth import AdminAuth
from app.config import settings
from app.database import engine
from app.models import User, CitizenRequest, RequestType, Proof

_USER_COLUMNS = [
    User.id,
    User.telegram_id,
    User.telegram_name,
    User.username,
    User.password_hash,
    User.role,
    User.source,
    User.created_at,
]

_REQUEST_COLUMNS = [
    CitizenRequest.id,
    CitizenRequest.user_id,
    CitizenRequest.type_id,
    CitizenRequest.status,
    CitizenRequest.assigned_operator_id,
    CitizenRequest.assigned_executor_id,
    CitizenRequest.title,
    CitizenRequest.description,
    CitizenRequest.address,
    CitizenRequest.photo_file_id,
    CitizenRequest.rating,
    CitizenRequest.citizen_confirmed,
    CitizenRequest.citizen_review,
    CitizenRequest.created_at,
    CitizenRequest.updated_at,
]

_REQUEST_TYPE_COLUMNS = [
    RequestType.id,
    RequestType.name,
    RequestType.slug,
]

_PROOF_COLUMNS = [
    Proof.id,
    Proof.request_id,
    Proof.executor_id,
    Proof.operator_id,
    Proof.file_ref,
    Proof.comment,
    Proof.status,
    Proof.created_at,
]


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_list = _USER_COLUMNS
    column_details_list = _USER_COLUMNS
    column_searchable_list = [User.username, User.telegram_id]
    column_sortable_list = [User.id, User.role, User.created_at]
    form_columns = _USER_COLUMNS


class CitizenRequestAdmin(ModelView, model=CitizenRequest):
    name = "Заявка"
    name_plural = "Заявки"
    icon = "fa-solid fa-file-lines"
    column_list = _REQUEST_COLUMNS
    column_details_list = _REQUEST_COLUMNS
    column_searchable_list = [CitizenRequest.title, CitizenRequest.description, CitizenRequest.address]
    column_sortable_list = [
        CitizenRequest.id,
        CitizenRequest.status,
        CitizenRequest.created_at,
        CitizenRequest.updated_at,
    ]
    form_columns = _REQUEST_COLUMNS


class RequestTypeAdmin(ModelView, model=RequestType):
    name = "Тип заявки"
    name_plural = "Типы заявок"
    icon = "fa-solid fa-tag"
    column_list = _REQUEST_TYPE_COLUMNS
    column_details_list = _REQUEST_TYPE_COLUMNS
    column_searchable_list = [RequestType.name, RequestType.slug]
    column_sortable_list = [RequestType.id, RequestType.name, RequestType.slug]
    form_columns = _REQUEST_TYPE_COLUMNS


class ProofAdmin(ModelView, model=Proof):
    name = "Пруф"
    name_plural = "Пруфы"
    icon = "fa-solid fa-image"
    column_list = _PROOF_COLUMNS
    column_details_list = _PROOF_COLUMNS
    column_sortable_list = [Proof.id, Proof.status, Proof.created_at]
    form_columns = _PROOF_COLUMNS


def setup_admin(app) -> AdminApp:
    admin = Admin(
        app,
        engine,
        base_url="/admin",
        title="Платформа помощи гражданам",
        authentication_backend=AdminAuth(settings.secret_key),
    )
    admin.add_view(UserAdmin)
    admin.add_view(CitizenRequestAdmin)
    admin.add_view(RequestTypeAdmin)
    admin.add_view(ProofAdmin)
    return admin
