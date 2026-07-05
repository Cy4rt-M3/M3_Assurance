"""Simple CLI Calculator"""

def calculate(a:float, op:str, b:float):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
    elif op == "%":
        return a % b
    elif op == "**":
        return a ** b
    else:
        raise ValueError(f"Unknown operator: {op}")


def main():
    print("=== CLI Calculator ===")
    print("Operators: + - * / % ** (or 'q' to quit)\n")

    while True:
        expr = input(">> ").strip()

        if expr.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            break

        if not expr:
            continue

        parts = expr.split()
        if len(parts) != 3:
            print("Format: <number> <operator> <number>  e.g. 5 + 3")
            continue

        num1_str, op, num2_str = parts

        try:
            num1 = float(num1_str)
            num2 = float(num2_str)
            result = calculate(num1, op, num2)

            if result == int(result):
                result = int(result)
            print(f"= {result}\n")

        except ValueError as e:
            print(f"Error: {e}\n")
        except ZeroDivisionError as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()