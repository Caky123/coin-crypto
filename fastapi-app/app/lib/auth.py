from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from app.config import ALGORITHM, API_KEY, SECRET_KEY, get_db
from app.db.schema import User
from app.models.token import TokenData
from app.models.user import UserInDB, UserResponse
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"me": "Read information about the current user.", "crypto": "Read coins."},
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Function for verify cron api key (aut. change price)
def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-KEY")
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Invalid API Key")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, email: str, no_passwd: bool = True):
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        if no_passwd:
            return db_user
        else:
            return UserInDB(**db_user.to_dict(include_password=True))


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username, no_passwd=False)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, email=email)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(
    current_user: Annotated[UserResponse, Security(get_current_user)],
):
    return current_user
