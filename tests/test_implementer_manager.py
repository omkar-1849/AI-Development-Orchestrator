from src.implementer.mock_implementer import MockImplementer
from src.implementer.implementer_session import ImplementerSession
from src.implementer.implementer_manager import ImplementerManager


def test_manager():

    implementer = MockImplementer()

    session = ImplementerSession(
        project_name="TestProject"
    )

    manager = ImplementerManager(
        implementer,
        session
    )

    result1 = manager.execute_task(
        "Create the backend structure"
    )

    print(result1.output)

    result2 = manager.execute_task(
        "Create the authentication module"
    )

    print(result2.output)


if __name__ == "__main__":
    test_manager()