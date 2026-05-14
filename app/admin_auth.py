from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.auth import verify_password
from app.database import async_session_factory
from app.models import User
from app.models.user import UserRole

_ADMIN_SESSION_USER_ID = "admin_user_id"


class AdminAuth(AuthenticationBackend):
    """Вход в /admin по username + password пользователя с ролью superuser."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            return False
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.username == str(username)))
            user = result.scalar_one_or_none()
        if user is None or not user.password_hash:
            return False
        if user.role != UserRole.superuser:
            return False
        if not verify_password(str(password), user.password_hash):
            return False
        request.session[_ADMIN_SESSION_USER_ID] = user.id
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get(_ADMIN_SESSION_USER_ID))
