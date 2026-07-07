import runpy
from unittest.mock import patch

from apps.calculator import (
    add,
    divide,
    get_numbers,
    main,
    modulus,
    multiply,
    power,
    process_choice,
    show_menu,
    subtract,
)


def test_add() -> None:
    assert add(2, 3) == 5


def test_subtract() -> None:
    assert subtract(5, 3) == 2


def test_multiply() -> None:
    assert multiply(4, 3) == 12


def test_divide() -> None:
    assert divide(10, 2) == 5


def test_divide_zero() -> None:
    assert divide(5, 0) == "Error: Cannot divide by zero."


def test_modulus() -> None:
    assert modulus(10, 3) == 1


def test_modulus_zero() -> None:
    assert modulus(5, 0) == "Error: Cannot perform modulus by zero."


def test_power() -> None:
    assert power(2, 3) == 8


def test_process_choice() -> None:
    with (
        patch("apps.calculator.get_numbers", return_value=(4, 5)),
        patch("builtins.print") as mock_print,
    ):
        process_choice("1")
        mock_print.assert_called_with("Result: 9")


def test_invalid_choice() -> None:
    with patch("builtins.print") as mock_print:
        process_choice("9")
        mock_print.assert_called_with("Invalid choice. Try again.")


def test_show_menu() -> None:
    with patch("builtins.print") as mock_print:
        show_menu()
        assert mock_print.call_count == 8


def test_get_numbers_success() -> None:
    with patch("builtins.input", side_effect=["10", "20"]):
        assert get_numbers() == (10.0, 20.0)


def test_get_numbers_invalid() -> None:
    with (
        patch("builtins.input", side_effect=["abc"]),
        patch("builtins.print") as mock_print,
    ):
        assert get_numbers() is None
        mock_print.assert_called_with("Please enter valid numbers.")


def test_process_choice_get_numbers_none() -> None:
    with patch("apps.calculator.get_numbers", return_value=None):
        assert process_choice("1") is None


def test_main_exit() -> None:
    with (
        patch("builtins.input", side_effect=["7"]),
        patch("builtins.print") as mock_print,
    ):
        main()

    mock_print.assert_any_call("Goodbye!")


def test_main_process_choice() -> None:
    with (
        patch("builtins.input", side_effect=["1", "7"]),
        patch("apps.calculator.get_numbers", return_value=(4, 5)),
        patch("builtins.print") as mock_print,
    ):
        main()

    mock_print.assert_any_call("Result: 9")


def test_calculator_script_execution() -> None:
    with (
        patch("builtins.input", side_effect=["7"]),
        patch("builtins.print"),
    ):
        runpy.run_module("apps.calculator", run_name="__main__")
