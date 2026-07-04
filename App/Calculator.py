def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float | str:
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b


def display_menu() -> None:
    print("\nPython CLI Calculator")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")
    print("5. Exit")


def get_numbers() -> tuple[float, float]:
    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))
    return a, b


def calculate(choice: str, a: float, b: float) -> float | str:
    if choice == "1":
        return add(a, b)
    if choice == "2":
        return subtract(a, b)
    if choice == "3":
        return multiply(a, b)
    return divide(a, b)


def main() -> None:
    while True:
        display_menu()

        choice = input("Enter your choice (1-5): ")

        if choice == "5":
            print("Goodbye!")
            break

        if choice not in {"1", "2", "3", "4"}:
            print("Invalid choice!")
            continue

        a, b = get_numbers()
        result = calculate(choice, a, b)
        print("Result:", result)


if __name__ == "__main__":
    main()