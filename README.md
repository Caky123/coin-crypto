Crypto Project:

How to run: docker-compose up --build

Visit: http://127.0.0.1:5001/

    Register a new user.

    Log in with email and password.

    Click on "Search" and you can find a crypto coin by its symbol (eth, btc, git, etc...).

    Click on "Add" and the coin will be added to your dashboard.

Symbols are validated by the CoinGecko API. The symbols are stored in Redis for fast access and validation. The prices are updated regularly via the CoinGecko API, which is called every 10 minutes by a cron job.

Data is stored in PostgreSQL.

The API of this application also allows you to update coins, but the update functionality is not yet implemented in Flask.
