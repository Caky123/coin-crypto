import logging
from typing import Annotated, List

import redis
from app.config import get_db, get_redis
from app.db.schema import Coin, User
from app.lib.auth import get_current_active_user
from app.lib.coin import get_coin_price
from app.lib.redis import get_coin_by_id, get_coins_by_symbol
from app.models.coin import CoinBase
from app.models.user import UserResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/coin/")
async def portfolio_coin(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user.coins

    except HTTPException as e:
        db.rollback()
        logging.error(f"HTTP Exception: {str(e)}")
        raise e

    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/coin/search/", response_model=List[CoinBase])
async def search_coin(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    coin_cymbol: str,
    redis_conn: redis.StrictRedis = Depends(get_redis),
):
    logging.debug(f"UserId: <{current_user.id}> search <{coin_cymbol}>")
    coins_for_symbol = await get_coins_by_symbol(coin_cymbol, redis_conn)
    if coins_for_symbol:
        return coins_for_symbol
    else:
        raise HTTPException(status_code=404, detail="Coin not found")


@router.post("/coin/add/")
async def add_coin(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    coin_text_id: str,
    db: Session = Depends(get_db),
    redis_conn: redis.StrictRedis = Depends(get_redis),
    currency: str = "usd",
):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        coin = db.query(Coin).filter(Coin.id_text == coin_text_id).first()

        if not coin:
            coin_redis = await get_coin_by_id(coin_text_id, redis_conn)

            if not coin_redis:
                raise HTTPException(status_code=404, detail="Coin data not found")

            # Get actual coin price
            coin_price = await get_coin_price(coin_text_id)

            if coin_text_id not in coin_price or currency not in coin_price[coin_text_id]:
                logging.warning("API did not return value")

            price = coin_price.get(coin_text_id, {}).get(currency, 0.0)

            # Create new coin to database
            new_coin = Coin(
                id_text=coin_text_id,
                symbol=coin_redis.get("symbol"),
                name=coin_redis.get("name"),
                price=price,
            )
            db.add(new_coin)
            coin = new_coin

        # Add coin to user portfolio
        user.coins.append(coin)
        db.commit()

        return {"message": "Coin added to user portfolio successfully"}

    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {str(e)}")
        raise HTTPException(status_code=409, detail="Coin already assigned to this user")

    except HTTPException as e:
        db.rollback()
        logging.error(f"HTTP Exception: {str(e)}")
        raise e

    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.put("/coin/update/{from_coin_text_id}/{to_coin_text_id}")
async def update_coin(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    from_coin_text_id: str,
    to_coin_text_id: str,
    db: Session = Depends(get_db),
    redis_conn: redis.StrictRedis = Depends(get_redis),
    currency: str = "usd",
):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        actual_coin = db.query(Coin).filter(Coin.id_text == from_coin_text_id).first()
        if not actual_coin:
            raise HTTPException(status_code=404, detail="Actual coin not found")

        new_coin = db.query(Coin).filter(Coin.id_text == to_coin_text_id).first()

        if actual_coin in user.coins:
            user.coins.remove(actual_coin)
        else:
            raise HTTPException(status_code=404, detail="Actual coin data not assigned to portfolio")

        if not new_coin:
            coin_redis = await get_coin_by_id(to_coin_text_id, redis_conn)
            if not coin_redis:
                raise HTTPException(status_code=404, detail="Coin data not found")

            coin_price = await get_coin_price(to_coin_text_id)
            if to_coin_text_id not in coin_price or currency not in coin_price[to_coin_text_id]:
                raise HTTPException(status_code=500, detail="Unable to fetch coin price")

            price = coin_price.get(to_coin_text_id, {}).get(currency, 0.0)

            new_coin = Coin(
                id_text=to_coin_text_id,
                symbol=coin_redis.get("symbol"),
                name=coin_redis.get("name"),
                price=price,
            )

            new_coin.price = price

            db.add(new_coin)

        user.coins.append(new_coin)

        db.commit()

        return {"message": "Coin updated successfully in the user portfolio"}

    except IntegrityError as e:
        db.rollback()
        logging.error(f"IntegrityError: {str(e)}")
        raise HTTPException(status_code=409, detail="Coin already assigned to this user")

    except HTTPException as e:
        db.rollback()
        logging.error(f"HTTP Exception: {str(e)}")
        raise e

    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.delete("/coin/remove/{coin_text_id}")
async def remove_coin(
    current_user: Annotated[UserResponse, Depends(get_current_active_user)],
    coin_text_id: str,
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        coin = db.query(Coin).filter(Coin.id_text == coin_text_id).first()
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found")

        if coin in user.coins:
            user.coins.remove(coin)
        else:
            raise HTTPException(status_code=400, detail="Coin is not in user's portfolio")

        db.commit()

        return {"message": "Coin removed from user portfolio successfully"}

    except HTTPException as e:
        db.rollback()
        logging.error(f"HTTP Exception: {str(e)}")
        raise e

    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
