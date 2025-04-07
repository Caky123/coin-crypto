import logging
import os
from time import sleep
from typing import List, Tuple

import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

API_COIN_KEY = os.getenv("COINGECKO_KEY")
API_COIN_URL = os.getenv("COINGECKO_URL")

# Connect
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


def get_coin_price(coin_ids_text, currency="usd"):
    url = API_COIN_URL + "simple/price?ids=" + coin_ids_text + "&vs_currencies=" + currency
    payload = {}
    headers = {"x-cg-api-key": API_COIN_KEY}

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        if response.status_code == 200:
            try:
                response_json = response.json()
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


def update_database(update_ids: List[Tuple[str, float]], conn: psycopg2.extensions.connection):
    batch_size = 20
    cursor = conn.cursor()

    for i in range(0, len(update_ids), batch_size):
        batch_ids = update_ids[i : i + batch_size]
        update_values = []

        for id_text, price in batch_ids:
            update_values.append((price, id_text))

        if update_values:
            try:
                update_query = """
                    UPDATE coins
                    SET price = %s
                    WHERE id_text = %s
                """
                cursor.executemany(update_query, update_values)
                logging.info(f"Updated {len(update_values)} rows in this batch.")

                conn.commit()

            except Exception as e:
                logging.error(f"Error during batch update: {e}")
                conn.rollback()
    cursor.close()


def run_cron_task():
    currency = "usd"
    query = """
            SELECT id_text
            FROM coins
            WHERE last_updated < NOW() - INTERVAL '2 HOURS';
            """

    cursor.execute(query)
    rows = cursor.fetchall()

    if rows:
        ids = [str(row[0]) for row in rows]

        grouped_ids = []

        # Call coingecko with max 20 crypto id
        for i in range(0, len(ids), 20):
            batch = ids[i : i + 20]
            grouped_ids.append(", ".join(batch))

            for group_id in grouped_ids:
                coin_price = get_coin_price(group_id)

                update_ids = []
                for id_text in batch:
                    if id_text not in coin_price or currency not in coin_price[id_text]:
                        logging.warning("API did not return value")
                    else:
                        if len(update_ids) > 20:
                            update_database(update_ids)
                            update_ids.clear()

                        price = coin_price.get(id_text, {}).get(currency, 0.0)
                        update_ids.append((id_text, price))

        if len(update_ids) > 20:
            update_database(update_ids)
    else:
        logging.info("No rows older than 2 hours.")


if __name__ == "__main__":
    while True:
        run_cron_task()
        sleep(600)  # Sleep 10 minutes
