from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.token import TokenResponse
from app.schemas.user import UserLogin, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserRegister) -> TokenResponse:
        if await self.repo.get_by_phone(data.phone):
            raise ConflictError("Phone number already registered")

        user = User(
            name=data.name,
            phone=data.phone,
            password_hash=hash_password(data.password),
        )
        await self.repo.save(user)
        return self._generate_tokens(user.id)

    async def login(self, data: UserLogin) -> TokenResponse:
        user = await self.repo.get_by_phone(data.phone)
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Incorrect phone number or password")
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        return self._generate_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        user_id = decode_token(refresh_token)
        if not user_id:
            raise UnauthorizedError("Invalid refresh token")
        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found")
        return self._generate_tokens(user.id)

    def _generate_tokens(self, user_id: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
