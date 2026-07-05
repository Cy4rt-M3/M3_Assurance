from unittest.mock import patch

import pytest

from apps.Calculator import Calculator, main


def test_add() -> None:
    calc = Calculator()
    assert calc.add(10, 5) == 15.0


def test_subtract() -> None:
    calc = Calculator()
    assert calc.subtract(10, 5) == 5.0


def test_multiply() -> None:
    calc = Calculator()
    assert calc.multiply(10, 5) == 50.0


def test_divide() -> None:
    calc = Calculator()
    assert calc.divide(10, 5) == 2.0


def test_divide_by_zero() -> None:
    calc = Calculator()
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calc.divide(10, 0)


def test_main_add(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("builtins.input", side_effect=["1", "10", "5"]):
        main()
    assert "15.0" in capsys.readouterr().out


def test_main_subtract(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("builtins.input", side_effect=["2", "10", "5"]):
        main()
    assert "5.0" in capsys.readouterr().out


def test_main_multiply(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("builtins.input", side_effect=["3", "10", "5"]):
        main()
    assert "50.0" in capsys.readouterr().out


def test_main_divide(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("builtins.input", side_effect=["4", "10", "5"]):
        main()
    assert "2.0" in capsys.readouterr().out


def test_main_invalid_choice(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("builtins.input", side_effect=["9"]):
        main()
    assert "Invalid choice" in capsys.readouterr().out


def test_main_entrypoint() -> None:
    with patch("builtins.input", side_effect=["1", "10", "5"]):
        with patch("apps.Calculator.__name__", "__main__"):
            import runpy

            runpy.run_module("apps.Calculator", run_name="__main__")
