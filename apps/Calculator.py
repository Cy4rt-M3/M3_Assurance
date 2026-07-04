class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main():
    calc = Calculator()

    print("Python CLI Calculator")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")

    choice = input("Choose operation (1-4): ")

    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))

    if choice == "1":
        print("Result:", calc.add(a, b))
    elif choice == "2":
        print("Result:", calc.subtract(a, b))
    elif choice == "3":
        print("Result:", calc.multiply(a, b))
    elif choice == "4":
        print("Result:", calc.divide(a, b))
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
