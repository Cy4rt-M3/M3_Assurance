def add(num1: float, num2: float) -> float:
    """Return the sum of two numbers."""
    return num1 + num2


def subtract(num1: float, num2: float) -> float:
    """Return the difference between two numbers."""
    return num1 - num2


def multiply(num1: float, num2: float) -> float:
    """Return the product of two numbers."""
    return num1 * num2


def divide(num1: float, num2: float) -> float:
    """Return the quotient of two numbers."""
    if num2 == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return num1 / num2


def get_operation(choice: str):
    """Return operation details based on user choice."""
    operations = {
        "1": ("+", add),
        "2": ("-", subtract),
        "3": ("*", multiply),
        "4": ("/", divide),
    }
    return operations.get(choice)


def main() -> None:
    """Run the calculator program."""
    print("Python CLI Calculator")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")

    choice = input("Enter choice (1/2/3/4): ")

    operation_data = get_operation(choice)

    if operation_data is None:
        print("Invalid choice")
        return

    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))

    symbol, operation = operation_data

    try:
        result = operation(num1, num2)
        print(f"{num1} {symbol} {num2} = {result}")
        print("Thank you for using Python CLI Calculator!")
    except ZeroDivisionError as error:
        print(error)


if __name__ == "__main__":
    main()
