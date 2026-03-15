from src.auth.user_repo import UserRepository
from src.auth.schemas.user import UserCreate, UserLoginEmail, UserUpdate,  UserLoginUsername, UserRead
from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from src.core.security import get_password_hash, verify_password
from src.exceptions import UsernameAlreadyInUse, UserAlreadyExistsError, InvalidCredentialsError, TokenError
from shared_packages.core.security import create_access_token
from src.auth.schemas.token import Token, TokenUser
from jose.jwt import decode, JWTError
from shared_packages.core.config import SharedBaseSettings
from sqlalchemy.ext.asyncio import AsyncSession
settings = SharedBaseSettings()
from sqlalchemy import func, select
from uuid import UUID
class AuthService:
    def __init__(self,session : AsyncSession,  userRepo: UserRepository):
        self.user_repo = userRepo
        self.session = session
    def _generate_token_response(self, user) -> dict:
        access_token = create_access_token(
            data={
                "sub": str(user.id), 
                "email": user.email 
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}
    async def register_user(self, user_data: UserCreate):
        if await  self.user_repo.find_user_email(user_data.email):
            raise UserAlreadyExistsError("Email already in use")

    
        if await self.user_repo.find_username(user_data.username):
            raise UsernameAlreadyInUse("Username aalready in use")
        try:
            new_user = await self.user_repo.create_user(user_data)
            await self.session.commit()
            await self.session.refresh(new_user)
            return new_user
        except Exception as e:
            self.session.rollback()
            raise e
        
    async def login_with_email(self, user_data:UserLoginEmail ) -> Token:
        user  = await self.user_repo.find_user_email(user_email=user_data.email)
        if not user  or not verify_password(user_data.password.get_secret_value(), user.hashed_password):
            raise InvalidCredentialsError("Wrong email or password")
        return self._generate_token_response(user)
    
    async def login_with_username(self, user_data:UserLoginUsername ) -> Token:
        user  = await self.user_repo.find_username(username=user_data.username)
        print(f"DEBUG: User found: {user.username if user else 'None'}")
        if not user  or not verify_password(user_data.password.get_secret_value(), user.hashed_password):
           raise InvalidCredentialsError("Wrong username or password")
        return self._generate_token_response(user)
    
    
    async def get_user_from_token(self, token : Token)-> TokenUser:
        try:
            payload = decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            username = payload.get("username")
            if not user_id:
                raise TokenError("Invalid token payload")
        except JWTError:
            raise TokenError("Could not verify credentials")
        return TokenUser(id=UUID(user_id), username=username)
    async def update_profile(self, user_id : UUID, update_data : UserUpdate) -> UserRead:
        data_to_update = update_data.model_dump(exclude_unset=True)
    
        if not data_to_update:
            return await self.user_repo.find_user_by_id(user_id)
        try:
            return await self.user_repo.update_user_by_id(user_id, data_to_update)
        except IntegrityError:
            raise UsernameAlreadyInUse("Username already in use")