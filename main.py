"""Wordle-style terminal game with a PostgreSQL backend.

Run:  python main.py
"""
import os

import psycopg2

import db
from game import (
    GREEN, MAX_ATTEMPTS, PURPLE, RESET, WORD_LENGTH,
    ask_guess, colorize, load_answers, load_valid_guesses, print_rules, score_guess,
)

# Enables ANSI colors in older Windows terminals
if os.name == "nt":
    os.system("")


def play_round(cur, player_id, valid_guesses):
    word_id, answer, definition = db.pick_word(cur, player_id)

    print(f"\nGuess the {WORD_LENGTH}-letter word. You have {MAX_ATTEMPTS} attempts.")
    print(f"{GREEN}Green{RESET} = right place, {PURPLE}Purple{RESET} = wrong place, "
          f"plain = not in word.\n")

    history = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"Attempt {attempt}/{MAX_ATTEMPTS}")
        guess = ask_guess(valid_guesses)
        result = score_guess(guess, answer)
        history.append(colorize(guess, result))

        print()
        for line in history:          # running board of all guesses so far
            print("   ", line)
        print()

        if all(r == "green" for r in result):
            print(f"{GREEN}Congratulations! You guessed it: {answer.upper()}{RESET}")
            if definition:
                print(f"Meaning: {definition}")
            db.save_game(cur, player_id, word_id, True, attempt)
            return

    print(f"Out of attempts! The word was {GREEN}{answer.upper()}{RESET}.")
    if definition:
        print(f"Meaning: {definition}")
    db.save_game(cur, player_id, word_id, False, MAX_ATTEMPTS)


def show_stats(cur, player_id):
    played, wins, avg = db.get_stats(cur, player_id)
    rate = f"{wins / played:.0%}" if played else "-"
    print(f"\nYour stats: played {played}, won {wins}, win rate {rate}, "
          f"average attempts on wins: {avg if avg is not None else '-'}")

    dist = db.get_guess_distribution(cur, player_id)
    if dist:
        print("Wins by number of attempts:")
        for n in range(1, MAX_ATTEMPTS + 1):
            count = dist.get(n, 0)
            print(f"  {n}: {'#' * count} {count}")


def show_leaderboard(cur):
    rows = db.get_leaderboard(cur)
    print("\n--- Leaderboard (Top 10) ---")
    if not rows:
        print("No games played yet.")
    for rank, (name, wins, played) in enumerate(rows, start=1):
        print(f"{rank:>2}. {name:<15} wins: {wins:<3} played: {played}")


def main():
    print_rules()
    answers = load_answers()
    valid_guesses = load_valid_guesses(answers)

    conn = db.connect_with_retry()
    try:
        with conn.cursor() as cur:
            db.setup_database(cur, answers)

            username = input("Enter your username: ").strip().lower() or "guest"
            username = username[:db.USERNAME_MAX]
            player_id = db.get_or_create_player(cur, username)
            print(f"Welcome, {username}!")

            while True:
                print("\n1) Play  2) My stats  3) Leaderboard  4) Quit")
                choice = input("Choose: ").strip()
                if choice == "1":
                    play_round(cur, player_id, valid_guesses)
                elif choice == "2":
                    show_stats(cur, player_id)
                elif choice == "3":
                    show_leaderboard(cur)
                elif choice == "4":
                    print("Thanks for playing!")
                    break
                else:
                    print("Invalid choice.")
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")
    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
