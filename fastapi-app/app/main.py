import logging

import app.config as config
from app.lib.redis import initialize_redis
from app.routers.auth import router as auth_router
from app.routers.portfolio import router as user_crypto_router
from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    redis_conn = config.get_redis_connection()
    logging.debug("Checking Redis initialization...")
    await initialize_redis(redis_conn)


app.include_router(auth_router)
app.include_router(user_crypto_router)
