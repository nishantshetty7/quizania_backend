from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

# Pydantic model for user registration
class LoginUser(BaseModel):
    email: EmailStr
    password: str

class GoogleUser(BaseModel):
    email: EmailStr
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = ""
    image: Optional[str] = None

class User(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    phone_number: Optional[str] = None
    image: Optional[str] = None
    profile_pic: Optional[str] = None
    is_active: bool = True
    auth_type: str = "regular"


# Pydantic model for user authentication
class UserResponse(BaseModel):
    email: str
    first_name: str


# Pydantic model for JWT token
class Token(BaseModel):
    access_token: str