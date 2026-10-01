"""Pure game logic. No database code here, so it is easy to test."""
import csv
from collections import Counter
from pathlib import Path

MAX_ATTEMPTS = 5
WORD_LENGTH = 5

GREEN = "\033[1;92m"
PURPLE = "\033[1;95m"
RESET = "\033[0m"

BASE_DIR = Path(__file__).parent
ANSWERS_FILE = BASE_DIR / "answers.csv"
VALID_GUESSES_FILE = BASE_DIR / "valid_guesses.txt"


def print_rules():
    print(f"""
Rules:
  * Secret word has {WORD_LENGTH} letters, you get {MAX_ATTEMPTS} attempts.
  * {GREEN}GREEN{RESET}  = correct letter, correct position
  * {PURPLE}PURPLE{RESET} = letter is in the word, but in a different position
  * PLAIN  = letter is not in the word
  * All 5 green = "Congratulations!"
===================================================""")


def score_guess(guess: str, answer: str) -> list[str]:
    """Return 'green' / 'purple' / 'absent' for each letter.

    Pass 1 locks in greens. Pass 2 gives purple only to leftover letters,
    so repeated letters are counted correctly.
    """
    result = ["absent"] * WORD_LENGTH
    remaining = Counter()

    for i in range(WORD_LENGTH):
        if guess[i] == answer[i]:
            result[i] = "green"
        else:
            remaining[answer[i]] += 1

    for i in range(WORD_LENGTH):
        if result[i] != "green" and remaining[guess[i]] > 0:
            result[i] = "purple"
            remaining[guess[i]] -= 1

    return result


def colorize(guess: str, result: list[str]) -> str:
    parts = []
    for letter, status in zip(guess, result):
        letter = letter.upper()
        if status == "green":
            parts.append(f"{GREEN}{letter}{RESET}")
        elif status == "purple":
            parts.append(f"{PURPLE}{letter}{RESET}")
        else:
            parts.append(letter)
    return " ".join(parts)


def load_answers(path=ANSWERS_FILE) -> list[tuple[str, str]]:
    """Read (word, definition) pairs from the answers CSV."""
    with open(path, newline="", encoding="utf-8") as f:
        return [
            (row["word"].strip().lower(), row["definition"].strip())
            for row in csv.DictReader(f)
            if len(row["word"].strip()) == WORD_LENGTH
        ]


def load_valid_guesses(answers, path=VALID_GUESSES_FILE) -> set[str]:
    """Allowed guesses = every word in the guess file + all answer words."""
    words = {w for w, _ in answers}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if len(w) == WORD_LENGTH and w.isalpha():
                    words.add(w)
    except FileNotFoundError:
        print(f"Warning: '{path}' not found. Only answer words are accepted.")
    return words


def ask_guess(valid_guesses: set[str]) -> str:
    """Keep asking until the guess is valid (invalid guesses cost nothing)."""
    while True:
        guess = input("Your guess: ").strip().lower()
        if len(guess) != WORD_LENGTH or not guess.isalpha():
            print(f"Please enter exactly {WORD_LENGTH} letters (a-z).")
        elif guess not in valid_guesses:
            print("Not in word list, try again.")
        else:
            return guess
