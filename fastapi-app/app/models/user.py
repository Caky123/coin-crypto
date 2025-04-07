from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True


class UserInDB(UserResponse):
    password: str
