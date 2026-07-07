import pytest
from apps.apps.calculator import add, divide, multiply, subtract


@pytest.fixture(scope="session", autouse=True)
def seed_db():
    """Mock database seed fixture"""
    pass


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 3) == 2


def test_multiply():
    assert multiply(4, 3) == 12


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    assert divide(5, 0) == "Error: Cannot divide by zero"
