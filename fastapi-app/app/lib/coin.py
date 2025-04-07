import json
import logging

import requests
from app.config import API_COIN_KEY, API_COIN_URL


async def get_coin_data_by_symbol(symbol, redis_conn):
    symbol_key = f"symbol:{symbol}"

    coin_ids = redis_conn.lrange(symbol_key, 0, -1)

    coins = []
    for coin_id in coin_ids:
        coin_key = f"{coin_id}"
        coin_data = json.loads(redis_conn.get(coin_key))

        if coin_data:
            print(f"Načítám coin {coin_id}: {coin_data}")
            coin_data["coin_id"] = coin_id
            coins.append(coin_data)
    return coins


logging.basicConfig(level=logging.INFO)


async def get_coin_price(coin_ids_text, currency="usd"):
    url = API_COIN_URL + "simple/price?ids=" + coin_ids_text + "&vs_currencies=" + currency
    payload = {}
    headers = {"x-cg-api-key": API_COIN_KEY}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        if response.status_code == 200:
            try:
                # Try extract data
                response_json = response.json()
                # Check good format
                if isinstance(response_json, dict):
                    return response_json
                else:
                    logging.error(f"Unexpected response format: {response_json}")
                    return {}

            except ValueError as e:
                logging.error(f"Error parsing JSON response: {e}")
                return {}
        else:
            logging.error(f"Failed to fetch data. Status code: {response.status_code}, Response: {response.text}")
            return {}
    except requests.exceptions.Timeout:
        logging.error("Request timeout")
        return {}
    except requests.exceptions.TooManyRedirects:
        logging.error("Too many redirects")
        return {}
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return {}


async def download_coins_list_data():
    url = API_COIN_URL + "coins/list"
    payload = {}
    headers = {"x-cg-api-key": API_COIN_KEY}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        if response.status_code == 200:
            try:
                response_json = response.json()

                if isinstance(response_json, list):
                    extracted_coins = [(coin["id"], coin["symbol"], coin["name"]) for coin in response_json]
                    return extracted_coins
                else:
                    logging.error(f"Unexpected response format: {response_json}")
                    return []

            except ValueError as e:
                logging.error(f"Error parsing JSON response: {e}")
                return []
        else:
            logging.error(f"Failed to fetch data. Status code: {response.status_code}, Response: {response.text}")
            return []
    except requests.exceptions.Timeout:
        logging.error("Request timeout")
        return []
    except requests.exceptions.TooManyRedirects:
        logging.error("Too many redirects")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return []
