from pydantic import BaseModel,   EmailStr, Field, SecretStr
from uuid import UUID
from shared_packages.schemas.base import CoreModel
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CoreModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra='ignore'
    )
class UserBase(CoreModel):
    email:  EmailStr
    username: str = Field(..., min_length=3, max_length=50, examples=['cool_user_123'])

class UserCreate(UserBase):
    password: SecretStr = Field(..., min_length=8, description="Password must be 8 charactes long")

class UserRead(UserBase):
    id: UUID
    is_active: bool =True
    created_at : datetime
class UserLoginEmail(CoreModel):
    email: EmailStr
    password: SecretStr
class UserLoginUsername(CoreModel):
    username: str
    password: SecretStr
class UserLogin(UserLoginUsername):
    username: str
class UserUpdate(CoreModel):
    username : str
class UserShort(CoreModel):
    username: str 
