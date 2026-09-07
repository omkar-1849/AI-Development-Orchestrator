from src.automation.claude_launcher import find_claude


claude = find_claude()

if claude is None:
    raise RuntimeError("Claude not found")


for element in claude.descendants():

    try:
        info = element.element_info

        if (
            info.control_type == "Button"
            and info.name
            and "Claude responded:" in info.name
        ):

            print("\nFOUND CLAUDE RESPONSE MARKER\n")
            print("Marker:")
            print(info.name)

            print("\n--- PARENT ---")

            parent = element.parent()

            if parent:
                print(
                    parent.element_info.control_type,
                    "-",
                    repr(parent.element_info.name)
                )

                print("\n--- CHILDREN OF PARENT ---")

                for child in parent.descendants():

                    child_info = child.element_info

                    print(
                        child_info.control_type,
                        "-",
                        repr(child_info.name)
                    )

            print("\n====================\n")

    except Exception:
        continue