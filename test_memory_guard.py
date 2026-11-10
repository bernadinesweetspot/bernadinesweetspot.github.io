import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

project_folder = Path(__file__).resolve().parent
data_folder = project_folder / "pebble_data"

with tempfile.TemporaryDirectory(prefix="pebble_guard_test_") as temporary_folder:

    test_folder = Path(temporary_folder)
    test_data_folder = test_folder / "pebble_data"

    test_data_folder.mkdir()

    # Copy Pebble's Python program.
    shutil.copy2(
        project_folder / "pebble.py",
        test_folder / "pebble.py"
    )

    # Copy all three data files.
    for filename in ["memory.json", "diary.json", "state.json"]:
        shutil.copy2(
            data_folder / filename,
            test_data_folder / filename
        )

    # Load the temporary memory file.
    test_memory_path = test_data_folder / "memory.json"

    with test_memory_path.open("r", encoding="utf-8") as file:
        memory_data = json.load(file)

    # Introduce an invalid connection to a nonexistent memory.
    memory_data["memories"][0]["connections"].append(999)

    with test_memory_path.open("w", encoding="utf-8") as file:
        json.dump(memory_data, file, indent=4)

    print("Created isolated test project.")
    print("Added an invalid connection to memory #1.")
    print("\nRunning the temporary copy of Pebble...\n")

    # Run Pebble using the temporary project folder.
    result = subprocess.run(
        [sys.executable, str(test_folder / "pebble.py")],
        cwd=test_folder,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print("--- Errors ---")
        print(result.stderr)

    # Check whether the safety guard worked.
    detected_problem = (
        "connects to missing or ambiguous memory #999"
        in result.stdout
    )

    displayed_warning = (
        "Pebble's memory data needs attention."
        in result.stdout
    )

    stopped_correctly = (
        "Stopping to prevent further changes."
        in result.stdout
    )

    skipped_prompts = (
        "Would you like Pebble to remember something?"
        not in result.stdout
    )

    print("--- Safety Test Results ---")
    print(f"Invalid connection detected: {detected_problem}")
    print(f"Warning displayed: {displayed_warning}")
    print(f"Shutdown message displayed: {stopped_correctly}")
    print(f"Normal prompts skipped: {skipped_prompts}")

    if all([
        detected_problem,
        displayed_warning,
        stopped_correctly,
        skipped_prompts
    ]):
        print("\nPASS: Pebble stopped safely after failed validation!")
    else:
        print("\nFAIL: The safety guard did not behave as expected.")

print("\nTemporary test project removed.")
