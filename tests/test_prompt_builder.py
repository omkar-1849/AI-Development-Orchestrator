from src.implementer.prompt_builder import ImplementerPromptBuilder


def test_prompt_builder():

    initial_prompt = ImplementerPromptBuilder.build_initial_prompt(
        "TestProject",
        "Create a FastAPI backend"
    )

    print("INITIAL PROMPT:")
    print(initial_prompt)

    task_prompt = ImplementerPromptBuilder.build_task_prompt(
        "Add JWT authentication"
    )

    print("\nTASK PROMPT:")
    print(task_prompt)


if __name__ == "__main__":
    test_prompt_builder()