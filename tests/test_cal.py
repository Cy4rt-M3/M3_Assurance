"""Tests for apps/cal.py — targets 100% branch + line coverage."""

import runpy

import pytest

from apps.cal import calculate, main


def _fake_input(response: str):  # type: ignore[return]
    """Typed factory returning a drop-in replacement for builtins.input."""

    def _inner(_prompt: str) -> str:
        return response

    return _inner


# ── calculate() ──────────────────────────────────────────────────────────────


def test_addition() -> None:
    assert calculate(10.0, "+", 5.0) == 15.0


def test_subtraction() -> None:
    assert calculate(10.0, "-", 3.0) == 7.0


def test_multiplication() -> None:
    assert calculate(4.0, "*", 3.0) == 12.0


def test_division() -> None:
    assert calculate(10.0, "/", 2.0) == 5.0


def test_invalid_operator_raises() -> None:
    with pytest.raises(ValueError, match="Invalid operator"):
        calculate(1.0, "%", 2.0)


def test_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        calculate(5.0, "/", 0.0)


# ── main() ───────────────────────────────────────────────────────────────────


def test_main_valid_expression(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", _fake_input("10 + 5"))
    main()
    captured = capsys.readouterr()
    assert "Result: 15.0" in captured.out


def test_main_invalid_format(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", _fake_input("10 +"))
    main()
    captured = capsys.readouterr()
    assert "Error:" in captured.out


def test_main_invalid_operator(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", _fake_input("10 % 5"))
    main()
    captured = capsys.readouterr()
    assert "Error:" in captured.out


def test_main_division_by_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("builtins.input", _fake_input("5 / 0"))
    main()
    captured = capsys.readouterr()
    assert "Error:" in captured.out


def test_main_guard(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Cover the `if __name__ == '__main__'` block (line 39)."""
    monkeypatch.setattr("builtins.input", _fake_input("2 + 2"))
    runpy.run_module("apps.cal", run_name="__main__")
    captured = capsys.readouterr()
    assert "Result: 4.0" in captured.out
