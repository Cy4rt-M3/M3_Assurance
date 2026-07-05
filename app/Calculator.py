from typing import Callable

Operation = Callable[[float, float], float | str]


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float | str:
    if b == 0:
        return "Cannot divide by zero"
    return a / b


OPERATIONS: dict[str, tuple[str, Operation]] = {
    "1": ("Addition", add),
    "2": ("Subtraction", subtract),
    "3": ("Multiplication", multiply),
    "4": ("Division", divide),
}


def main() -> None:
    print("Python CLI Calculator")

    for key, (name, _) in OPERATIONS.items():
        print(f"{key}. {name}")

    choice = input("Enter your choice (1-4): ")

    if choice not in OPERATIONS:
        print("Invalid choice")
        return

    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))

    _, operation = OPERATIONS[choice]
    result = operation(a, b)

    print("Result:", result)


if __name__ == "__main__":
    main()