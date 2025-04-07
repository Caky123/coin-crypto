# auth.py
from datetime import timedelta
from typing import Annotated

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, get_db
from app.db.schema import User
from app.lib.auth import (authenticate_user, create_access_token,
                          get_password_hash)
from app.models.token import Token
from app.models.user import UserCreate
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter(tags=["Authorization"])


@router.post("/register")
def register(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    # Zkontrolujete, zda už uživatel existuje
    email = form_data.username
    db_user = db.query(User).filter(User.email == email).first()

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(form_data.password)
    new_user = UserCreate(email=email, password=hashed_password)

    db_user = User(**new_user.dict())  # Convert to SQLAlchemy model

    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
) -> Token:
    email = form_data.username
    user = authenticate_user(db, email, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")
