import pytest
from pytest import CaptureFixture, MonkeyPatch

from apps.apps.calculator import (
    add,
    calculate,
    display_menu,
    divide,
    get_numbers,
    main,
    multiply,
    subtract,
)


@pytest.fixture(scope="session", autouse=True)
def seed_db() -> None:
    """Mock database seed fixture"""
    pass


def test_add() -> None:
    assert add(2, 3) == 5


def test_subtract() -> None:
    assert subtract(5, 3) == 2


def test_multiply() -> None:
    assert multiply(4, 3) == 12


def test_divide() -> None:
    assert divide(10, 2) == 5


def test_divide_by_zero() -> None:
    assert divide(5, 0) == "Error: Cannot divide by zero"


def test_display_menu(capsys: CaptureFixture[str]) -> None:
    display_menu()
    captured = capsys.readouterr()
    assert "Python CLI Calculator" in captured.out
    assert "5. Exit" in captured.out


def test_get_numbers(monkeypatch: MonkeyPatch) -> None:
    inputs = iter(["10", "5"])

    def fake_input(_: str) -> str:
        return next(inputs)

    monkeypatch.setattr("builtins.input", fake_input)
    a, b = get_numbers()
    assert a == 10
    assert b == 5


def test_calculate_add() -> None:
    assert calculate("1", 2, 3) == 5


def test_calculate_subtract() -> None:
    assert calculate("2", 5, 3) == 2


def test_calculate_multiply() -> None:
    assert calculate("3", 4, 3) == 12


def test_calculate_divide() -> None:
    assert calculate("4", 10, 2) == 5


def test_main_invalid_choice_then_exit(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    inputs = iter(["9", "5"])

    def fake_input(_: str) -> str:
        return next(inputs)

    monkeypatch.setattr("builtins.input", fake_input)
    main()
    captured = capsys.readouterr()
    assert "Invalid choice!" in captured.out
    assert "Goodbye!" in captured.out


def test_main_add_then_exit(
    monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    inputs = iter(["1", "2", "3", "5"])

    def fake_input(_: str) -> str:
        return next(inputs)

    monkeypatch.setattr("builtins.input", fake_input)
    main()
    captured = capsys.readouterr()
    assert "Result:" in captured.out
    assert "Goodbye!" in captured.out
