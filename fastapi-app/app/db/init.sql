-- The creation of a database structure in PostgreSQL.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE coins (
    id_text TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_coin_association (
    user_id INTEGER NOT NULL,
    coin_id_text TEXT NOT NULL,
    PRIMARY KEY (user_id, coin_id_text),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (coin_id_text) REFERENCES coins(id_text) ON DELETE CASCADE
);