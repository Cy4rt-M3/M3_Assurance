#!/usr/bin/env python3
from collections.abc import Callable

OPERATIONS: dict[str, Callable[[float, float], float]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
}


def calculate(a: float, operator: str, b: float) -> float:
    if operator not in OPERATIONS:
        raise ValueError("Invalid operator")
    if operator == "/" and b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return OPERATIONS[operator](a, b)


def main():
    print("Simple CLI Calculator")
    print("Usage: <number> <operator> <number>")
    print("Example: 10 + 5")

    try:
        expression = input("> ").split()
        if len(expression) != 3:
            raise ValueError("Invalid input format")

        left, operator, right = expression
        result = calculate(float(left), operator, float(right))
        print(f"Result: {result}")

    except Exception as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    main()
