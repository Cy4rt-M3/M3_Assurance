def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        return "Cannot divide by zero"
    return a / b


OPERATIONS = {
    "1": ("Addition", add),
    "2": ("Subtraction", subtract),
    "3": ("Multiplication", multiply),
    "4": ("Division", divide),
}


def main():
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
    print("Result:", operation(a, b))


if __name__ == "__main__":
    main()

    