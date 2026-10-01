import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import game
from game import colorize, load_answers, load_valid_guesses, score_guess


def test_all_green():
    assert score_guess("apple", "apple") == ["green"] * 5


def test_all_absent():
    assert score_guess("brick", "ghost") == ["absent"] * 5


def test_purple_wrong_position():
    assert score_guess("eaglx", "apple")[:2] == ["purple", "purple"]


def test_repeated_letter_in_guess_only_one_in_answer():
    # answer has one 'e'; guess has two. Only one can be coloured.
    assert score_guess("speed", "abide") == [
        "absent", "absent", "purple", "absent", "purple"]


def test_repeated_letters_double_l():
    assert score_guess("llama", "hello") == [
        "purple", "purple", "absent", "absent", "absent"]


def test_green_takes_priority_over_purple():
    # 'hello' has two l's. Guess "alloy": 3rd letter is green, 2nd is purple.
    result = score_guess("alloy", "hello")
    assert result[2] == "green"
    assert result[1] == "purple"


def test_result_length_is_five():
    assert len(score_guess("train", "plant")) == game.WORD_LENGTH


def test_colorize_has_five_letters_and_colour_codes():
    out = colorize("apple", ["green", "purple", "absent", "absent", "absent"])
    assert game.GREEN in out and game.PURPLE in out
    assert out.count(game.RESET) == 2


def test_load_answers_reads_bundled_file():
    answers = load_answers()
    assert len(answers) > 50
    assert all(len(w) == 5 and w == w.lower() for w, _ in answers)


def test_valid_guesses_include_answers(tmp_path):
    f = tmp_path / "g.txt"
    f.write_text("hello\nABCDE\ntoolong\nab1de\n")
    valid = load_valid_guesses([("zebra", "x")], path=f)
    assert valid == {"zebra", "hello", "abcde"}


def test_missing_guess_file_falls_back_to_answers(tmp_path, capsys):
    valid = load_valid_guesses([("zebra", "x")], path=tmp_path / "nope.txt")
    assert valid == {"zebra"}
    assert "Warning" in capsys.readouterr().out
