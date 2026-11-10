import json
import shutil
from pathlib import Path

from pebble import delete_memory

# Locate the real memory file and temporary test file.
source_path = Path("pebble_data") / "memory.json"
test_path = Path("pebble_data") / "memory_deletion_test.json"

# Avoid accidentally overwriting an existing file.
if test_path.exists():
    print("ERROR: The temporary test file already exists.")
    raise SystemExit(1)

try:
    # Make a separate copy of Pebble's memories.
    shutil.copy2(source_path, test_path)

    print("Created a temporary copy of memory.json.")

    # Load the original test data.
    with test_path.open("r", encoding="utf-8") as file:
        original_data = json.load(file)

    # Record the original connections.
    original_memories = original_data["memories"]

    print("\nConnections before deletion:")

    for memory in original_memories:
        print(
            f"Memory #{memory['id']}: "
            f"{memory.get('connections', [])}"
        )

    # Check that memory #2 exists before testing.
    target_exists = any(
        memory.get("id") == 2
        for memory in original_memories
        if isinstance(memory, dict)
    )

    if not target_exists:
        print("\nERROR: Memory #2 does not exist in the test data.")
        raise SystemExit(1)

    # Delete memory #2 from the temporary copy.
    print("\nTesting deletion of memory #2...")

    deletion_result = delete_memory(test_path, 2)

    # Load the updated test data.
    with test_path.open("r", encoding="utf-8") as file:
        updated_data = json.load(file)

    updated_memories = updated_data["memories"]

    # Check that memory #2 was deleted.
    deleted_successfully = not any(
        memory.get("id") == 2
        for memory in updated_memories
        if isinstance(memory, dict)
    )

    # Check that no remaining memory refers to #2.
    connections_cleaned = all(
        2 not in memory.get("connections", [])
        for memory in updated_memories
        if isinstance(memory, dict)
        and isinstance(memory.get("connections", []), list)
    )

    print("\nConnections after deletion:")

    for memory in updated_memories:
        print(
            f"Memory #{memory['id']}: "
            f"{memory.get('connections', [])}"
        )

    print("\n--- Test Results ---")
    print(f"Deletion succeeded: {deleted_successfully}")
    print(f"Connections cleaned: {connections_cleaned}")

    if deletion_result and deleted_successfully and connections_cleaned:
        print("\nPASS: Memory deletion and connection cleanup work!")
    else:
        print("\nFAIL: Something went wrong during the test.")

finally:
    # Remove the temporary test file.
    if test_path.exists():
        test_path.unlink()
        print("\nTemporary test file removed.")
