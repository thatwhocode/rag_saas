from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from src.db.user  import User
from src.auth.schemas.user import UserBase, UserLogin, UserRead, UserCreate
from uuid import UUID
from src.core.security import get_password_hash
class UserRepository():
    def __init__(self, session:AsyncSession ) -> User | None:
        self.session = session

    async def find_user_email(self, user_email: str)-> UserRead | None:
        query = select(User).where(User.email == user_email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_username(self, username : str)-> UserRead | None:
        query = select(User).where(func.lower(User.username) == func.lower(username))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    
    async def create_user(self, user_data : UserCreate) -> User | None:
        new_user = User(
            email = user_data.email,
            username = user_data.username,
            hashed_password= get_password_hash(user_data.password.get_secret_value())
        )
        self.session.add(new_user)
        await self.session.flush()
        await self.session.refresh(new_user)
        return new_user
    async def find_user_by_id(self, user_id : UUID)-> UserRead:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_top_players(self, limit: int = 10):
        query = select(User).order_by(User.reputation.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_user_by_id(self, user_id : UUID, update_data: dict):
        query = (
        update(User)
        .where(User.id == user_id)
        .values(**update_data) 
        .returning(User)
    )
        return await self.session.execute(query)
    async def get_all_users(self, skip: int, limit: int):
        query = select(User).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
