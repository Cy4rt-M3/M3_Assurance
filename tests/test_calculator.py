"""
Unit tests for CyBreach CLI Calculator.
"""

import pytest
from app.Calculator import add, sub, mul, div, main

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(-2, -3) == -5
    assert add(2.5, 3.5) == 6.0

def test_sub():
    assert sub(5, 3) == 2
    assert sub(1, 5) == -4
    assert sub(-1, -1) == 0
    assert sub(5.5, 2.5) == 3.0

def test_mul():
    assert mul(2, 3) == 6
    assert mul(-2, 3) == -6
    assert mul(0, 5) == 0
    assert mul(1.5, 2) == 3.0

def test_div():
    assert div(6, 3) == 2.0
    assert div(-6, 3) == -2.0
    assert div(5, 2) == 2.5
    
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        div(5, 0)

def test_cli_add(capsys):
    exit_code = main(["add", "2", "3"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "5.0"

def test_cli_sub(capsys):
    exit_code = main(["sub", "10", "4"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "6.0"

def test_cli_mul(capsys):
    exit_code = main(["mul", "3", "4"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "12.0"

def test_cli_div(capsys):
    exit_code = main(["div", "10", "2"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "5.0"

def test_cli_div_by_zero(capsys):
    exit_code = main(["div", "10", "0"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Cannot divide by zero" in captured.err

def test_cli_invalid_args():
    # argparse raises SystemExit on parsing errors
    with pytest.raises(SystemExit):
        main(["add", "invalid"])

def test_cli_unknown_operation(monkeypatch, capsys):
    class MockArgs:
        operation = "unknown"
        num1 = 1.0
        num2 = 2.0
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self, argv: MockArgs())
    exit_code = main([])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Unknown operation" in captured.err

def test_subprocess_run():
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "app/Calculator.py", "add", "5", "3"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.stdout.strip() == "8.0"

