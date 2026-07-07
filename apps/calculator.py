"""Simple CLI Calculator"""


def add(a: float, b: float):
    return a + b


def subtract(a: float, b: float):
    return a - b


def multiply(a: float, b: float):
    return a * b


def divide(a: float, b: float):
    if b == 0:
        return "Error: Cannot divide by zero."
    return a / b


def modulus(a: float, b: float):
    if b == 0:
        return "Error: Cannot perform modulus by zero."
    return a % b


def power(a: float, b: float):
    return a**b


OPERATIONS = {
    "1": ("Add", add),
    "2": ("Subtract", subtract),
    "3": ("Multiply", multiply),
    "4": ("Divide", divide),
    "5": ("Modulus", modulus),
    "6": ("Power", power),
}


def show_menu():
    print("\nChoose an operation:")
    for key, (name, _) in OPERATIONS.items():
        print(f"{key}. {name}")
    print("7. Exit")


def get_numbers():
    try:
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
        return num1, num2
    except ValueError:
        print("Please enter valid numbers.")
        return None


def process_choice(choice: str):
    operation = OPERATIONS.get(choice)
    if operation is None:
        print("Invalid choice. Try again.")
        return

    numbers = get_numbers()
    if numbers is None:
        return

    num1, num2 = numbers
    _, func = operation
    print(f"Result: {func(num1, num2)}")


def main():
    print("=== CLI Calculator ===")

    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ")

        if choice == "7":
            print("Goodbye!")
            break

        process_choice(choice)


if __name__ == "__main__":
    main()
