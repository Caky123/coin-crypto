import os
from typing import Generator

import redis
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

API_COIN_KEY = os.getenv("COINGECKO_KEY")
API_COIN_URL = os.getenv("COINGECKO_URL")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

REDIS_LOCK_KEY = "redis_data_lock"

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

API_KEY = os.getenv("API_KEY", "default_secret_key")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 20))

# Ensure DATABASE_URL is set
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine and session factory
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for SQLAlchemy models
Base = declarative_base()


def get_db_session() -> Generator:
    """
    Dependency to provide a SQLAlchemy session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis_connection() -> redis.StrictRedis:
    """
    Dependency to provide a Redis connection.
    """
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


def get_db(db: Session = Depends(get_db_session)) -> Generator:
    """
    Dependency for using the database session within FastAPI endpoints.
    """
    yield db


def get_redis(redis_conn: redis.StrictRedis = Depends(get_redis_connection)) -> Generator:
    """
    Dependency for using the Redis connection within FastAPI endpoints.
    """
    yield redis_conn
