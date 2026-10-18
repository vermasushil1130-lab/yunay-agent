"""Entry point for math_toolkit: imports operations and prints results."""

from operations import add, multiply
from helper import format_result

A = 5
B = 3


def main():
    print(format_result(f"{A} + {B}", add(A, B)))
    print(format_result(f"{A} * {B}", multiply(A, B)))


if __name__ == "__main__":
    main()
