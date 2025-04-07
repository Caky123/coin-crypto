import logging

import app.config as config
from app.lib.coin import download_coins_list_data
from app.models.coin import CoinCreate


async def store_coin_by_id(coin_id, coin_data, redis_conn):
    redis_conn.hmset(f"coin:{coin_id}", coin_data)


async def store_coin_by_symbol(symbol, coin_id, redis_conn):
    redis_conn.sadd(f"symbol:{symbol}", coin_id)


async def get_coin_by_id(coin_id, redis_conn):
    coin = redis_conn.hgetall(f"coin:{coin_id}")
    return coin


async def get_coins_by_symbol(symbol, redis_conn):
    coin_ids = redis_conn.smembers(f"symbol:{symbol}")
    coins = []
    for coin_id in coin_ids:
        coin = redis_conn.hgetall(f"coin:{coin_id}")
        coins.append(coin)
    return coins


async def initialize_redis(redis_conn):
    # Try get key
    lock_acquired = redis_conn.setnx(config.REDIS_LOCK_KEY, "locked")
    if not lock_acquired:
        logging.debug("Lock already acquired by another server.")
        return

    # Expired after 10 minutes
    redis_conn.expire(config.REDIS_LOCK_KEY, 600)

    coins = await download_coins_list_data()

    if coins:
        logging.info(f"Get {len(coins)} coins.")

        for id, symbol, name in coins:
            coin_data = CoinCreate(id_text=id, name=name, symbol=symbol, price=0)

            await store_coin_by_id(id, coin_data.__dict__, redis_conn)
            await store_coin_by_symbol(symbol, id, redis_conn)

    else:
        logging.info("No coins found or there was an error.")
