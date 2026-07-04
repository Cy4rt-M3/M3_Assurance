"""
CyBreach Assurance Platform
CLI Calculator Exercise

This module provides basic arithmetic operations (addition, subtraction,
multiplication, division) accessible via a Command Line Interface (CLI).
"""

import argparse
import sys


def add(x: float, y: float) -> float:
    """Return the sum of x and y."""
    return x + y


def sub(x: float, y: float) -> float:
    """Return the difference of x and y."""
    return x - y


def mul(x: float, y: float) -> float:
    """Return the product of x and y."""
    return x * y


def div(x: float, y: float) -> float:
    """
    Return the quotient of x and y.

    Raises:
        ValueError: If y is zero (division by zero is undefined).
    """
    if y == 0:
        raise ValueError("Cannot divide by zero.")
    return x / y


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="CyBreach Assurance Platform CLI Calculator."
    )

    # Subparsers for commands
    subparsers = parser.add_subparsers(
        dest="operation", required=True, help="Arithmetic operation to perform"
    )

    # Parent parser for shared arguments to avoid redundancy
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("num1", type=float, help="The first operand")
    parent_parser.add_argument("num2", type=float, help="The second operand")

    # Add operations
    subparsers.add_parser("add", parents=[parent_parser], help="Add two numbers")
    subparsers.add_parser("sub", parents=[parent_parser], help="Subtract two numbers")
    subparsers.add_parser("mul", parents=[parent_parser], help="Multiply two numbers")
    subparsers.add_parser("div", parents=[parent_parser], help="Divide two numbers")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Execution entry point for CLI calculator."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Dictionary mapping to keep cyclomatic complexity <= 4
    operations = {
        "add": add,
        "sub": sub,
        "mul": mul,
        "div": div,
    }

    op_func = operations.get(args.operation)
    if not op_func:
        print(f"Unknown operation: {args.operation}", file=sys.stderr)
        return 1

    try:
        result = op_func(args.num1, args.num2)
        print(result)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
