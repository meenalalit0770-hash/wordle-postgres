# Wordle in the Terminal (Python + PostgreSQL)

A Wordle-style word-guessing game that runs in the terminal. Player accounts,
game history, personal stats and a leaderboard are stored in PostgreSQL.

## How to play

- Guess the secret 5-letter word in 5 attempts.
- **Green** = correct letter, correct position
- **Purple** = letter is in the word, but in a different position
- Plain = letter is not in the word
- Invalid or unknown words are rejected and don't use up an attempt.

```
Attempt 2/5
Your guess: speed

    A B I D E
    S P E E D
```

## Features

- Correct handling of repeated letters (two-pass scoring)
- Player accounts, created automatically on first login
- Never repeats a word you've already played until you've seen them all
- Stats: games played, win rate, average attempts, wins-by-attempts chart
- Top-10 leaderboard
- Guesses validated against a list of ~14,800 words
- Safe against SQL injection (parameterized queries)
- Database password read from an environment variable or a hidden prompt; never stored in code
- Unit tests for the scoring logic

## Tech

Python 3.9+, PostgreSQL, `psycopg2`, `pytest`.
SQL features used: foreign keys, `CHECK` constraints, indexes,
`ON CONFLICT DO NOTHING`, `RETURNING`, `FILTER` aggregates, `NOT EXISTS`.

## Project structure

```
main.py             menu and game loop
game.py             pure game logic (scoring, colours, word loading) - no database code
db.py               connection, schema and all SQL queries
answers.csv         secret words with definitions
valid_guesses.txt   all accepted guesses
tests/test_game.py  unit tests
```

## Database schema

```
players(id, username UNIQUE, created_at)
words(id, word UNIQUE, definition)
games(id, player_id -> players, word_id -> words, won, attempts, played_at)
```

Tables are created automatically on first run.

## Setup

1. Install [Python 3.9+](https://www.python.org/downloads/) and [PostgreSQL](https://www.postgresql.org/download/).
2. Create the database (once):
   ```sql
   CREATE DATABASE projectdb;
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the game:
   ```bash
   python main.py
   ```
   You'll be asked for your PostgreSQL password. To skip the prompt, set it first:

   | Shell | Command |
   |---|---|
   | PowerShell | `$env:DB_PASSWORD="yourpassword"` |
   | cmd | `set DB_PASSWORD=yourpassword` |
   | Mac / Linux | `export DB_PASSWORD=yourpassword` |

Optional settings (defaults in brackets): `DB_NAME` [projectdb], `DB_USER` [postgres],
`DB_HOST` [localhost], `DB_PORT` [5432].

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```
The tests cover the scoring logic and don't need a database.

## Design notes

- **Two-pass scoring:** greens are locked in first; purples are given only from the
  leftover letters of the answer. That is what makes `speed` vs `abide` come out right
  (only one of the two E's is marked).
- **Separation of concerns:** `game.py` has no database code, so it's testable on its own.
- **Autocommit:** each insert is a single statement, so autocommit avoids
  transactions getting stuck after an error.

## Ideas for next steps

- Daily word mode
- Letter keyboard showing used/eliminated letters
- Colour-blind friendly mode (symbols instead of colours)
- Web or GUI front end

## License

MIT
