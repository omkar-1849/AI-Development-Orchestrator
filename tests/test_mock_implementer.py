from src.implementer import MockImplementer


def test_mock_implementer():
    implementer = MockImplementer()

    result = implementer.execute(
        "Create a Python function that adds two numbers"
    )

    print(result)


if __name__ == "__main__":
    test_mock_implementer()