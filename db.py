"""All PostgreSQL code: connection, schema, and queries."""
import getpass
import os
import sys

import psycopg2

USERNAME_MAX = 30

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME", "projectdb"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(30) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS words (
    id         SERIAL PRIMARY KEY,
    word       VARCHAR(5) UNIQUE NOT NULL,
    definition TEXT,
    CHECK (char_length(word) = 5 AND word = lower(word))
);

CREATE TABLE IF NOT EXISTS games (
    id        SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    word_id   INT NOT NULL REFERENCES words(id),
    won       BOOLEAN NOT NULL,
    attempts  INT NOT NULL CHECK (attempts BETWEEN 1 AND 5),
    played_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_games_player ON games(player_id);
CREATE INDEX IF NOT EXISTS idx_games_word   ON games(word_id);
"""


def connect_with_retry(max_tries: int = 3):
    """Connect to PostgreSQL. Uses DB_PASSWORD if set, otherwise asks for it.

    A wrong password gives you another try instead of crashing.
    """
    config = dict(DB_CONFIG)
    for attempt in range(1, max_tries + 1):
        if not config["password"]:
            config["password"] = getpass.getpass(
                f"PostgreSQL password for user '{config['user']}': "
            )
        try:
            conn = psycopg2.connect(**config)
            conn.autocommit = True  # each statement saves immediately
            return conn
        except psycopg2.OperationalError as e:
            msg = str(e).strip()
            if "password authentication failed" in msg and attempt < max_tries:
                print("Wrong password, try again.")
                config["password"] = None
                continue
            sys.exit(f"Could not connect to the database: {msg}")


def setup_database(cur, answers):
    """Create tables (if missing) and add answer words (if missing)."""
    cur.execute(SCHEMA_SQL)
    cur.executemany(
        "INSERT INTO words (word, definition) VALUES (%s, %s) "
        "ON CONFLICT (word) DO NOTHING",
        answers,
    )


def get_or_create_player(cur, username: str) -> int:
    cur.execute("SELECT id FROM players WHERE username = %s", (username,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO players (username) VALUES (%s) RETURNING id", (username,)
    )
    return cur.fetchone()[0]


def pick_word(cur, player_id: int):
    """Prefer words this player hasn't played yet; otherwise any word."""
    cur.execute(
        """
        SELECT w.id, w.word, w.definition
        FROM words w
        WHERE NOT EXISTS (
            SELECT 1 FROM games g
            WHERE g.word_id = w.id AND g.player_id = %s
        )
        ORDER BY random() LIMIT 1
        """,
        (player_id,),
    )
    row = cur.fetchone()
    if row is None:
        cur.execute("SELECT id, word, definition FROM words ORDER BY random() LIMIT 1")
        row = cur.fetchone()
    return row


def save_game(cur, player_id, word_id, won, attempts):
    cur.execute(
        "INSERT INTO games (player_id, word_id, won, attempts) VALUES (%s, %s, %s, %s)",
        (player_id, word_id, won, attempts),
    )


def get_stats(cur, player_id):
    """Return (played, wins, avg_attempts_on_wins)."""
    cur.execute(
        """
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE won),
               ROUND(AVG(attempts) FILTER (WHERE won), 2)
        FROM games WHERE player_id = %s
        """,
        (player_id,),
    )
    return cur.fetchone()


def get_guess_distribution(cur, player_id):
    """Return {attempts: number_of_wins} for this player."""
    cur.execute(
        """
        SELECT attempts, COUNT(*) FROM games
        WHERE player_id = %s AND won
        GROUP BY attempts ORDER BY attempts
        """,
        (player_id,),
    )
    return dict(cur.fetchall())


def get_leaderboard(cur, limit: int = 10):
    """Return rows of (username, wins, played), best first."""
    cur.execute(
        """
        SELECT p.username,
               COUNT(*) FILTER (WHERE g.won) AS wins,
               COUNT(*)                      AS played
        FROM players p
        JOIN games g ON g.player_id = p.id
        GROUP BY p.id, p.username
        ORDER BY wins DESC, AVG(g.attempts) FILTER (WHERE g.won) ASC NULLS LAST, played ASC
        LIMIT %s
        """,
        (limit,),
    )
    return cur.fetchall()
