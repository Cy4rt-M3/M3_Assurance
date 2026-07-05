from collections.abc import Callable


class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main() -> None:
    calc = Calculator()

    operations: dict[str, tuple[str, Callable[[float, float], float]]] = {
        "1": ("Add", calc.add),
        "2": ("Subtract", calc.subtract),
        "3": ("Multiply", calc.multiply),
        "4": ("Divide", calc.divide),
    }

    print("Python CLI Calculator")
    for key, (name, _) in operations.items():
        print(f"{key}. {name}")

    choice = input("Choose operation (1-4): ")

    if choice not in operations:
        print("Invalid choice")
        return

    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))

    _, operation = operations[choice]
    print("Result:", operation(a, b))


if __name__ == "__main__":
    main()
