"""
Unit tests for CyBreach CLI Calculator.
"""

import argparse
import sys

import pytest

from app.Calculator import add, create_parser, div, main, mul, sub


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-2, -3) == -5
    assert add(2.5, 3.5) == 6.0


def test_sub() -> None:
    assert sub(5, 3) == 2
    assert sub(1, 5) == -4
    assert sub(-1, -1) == 0
    assert sub(5.5, 2.5) == 3.0


def test_mul() -> None:
    assert mul(2, 3) == 6
    assert mul(-2, 3) == -6
    assert mul(0, 5) == 0
    assert mul(1.5, 2) == 3.0


def test_div() -> None:
    assert div(6, 3) == 2.0
    assert div(-6, 3) == -2.0
    assert div(5, 2) == 2.5

    with pytest.raises(ValueError, match="Cannot divide by zero."):
        div(5, 0)


def test_cli_add(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["add", "2", "3"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "5.0"


def test_cli_sub(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["sub", "10", "4"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "6.0"


def test_cli_mul(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["mul", "3", "4"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "12.0"


def test_cli_div(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["div", "10", "2"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "5.0"


def test_cli_div_by_zero(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["div", "10", "0"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cannot divide by zero" in captured.err


def test_cli_invalid_args() -> None:
    # argparse raises SystemExit on parsing errors
    with pytest.raises(SystemExit):
        main(["add", "invalid"])


def test_cli_unknown_operation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class MockArgs:
        operation = "unknown"
        num1 = 1.0
        num2 = 2.0

    def mock_parse_args(
        self: argparse.ArgumentParser, argv: list[str] | None = None
    ) -> MockArgs:
        return MockArgs()

    monkeypatch.setattr("argparse.ArgumentParser.parse_args", mock_parse_args)
    exit_code = main([])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Unknown operation" in captured.err


def test_subprocess_run() -> None:
    import subprocess

    result = subprocess.run(
        [sys.executable, "app/Calculator.py", "add", "5", "3"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "8.0"


def test_parser_setup() -> None:
    parser = create_parser()
    assert parser.description is not None
