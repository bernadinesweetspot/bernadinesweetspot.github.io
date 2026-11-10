import json
import shutil
from pathlib import Path

from pebble import validate_existing_memories

source_path = Path("pebble_data") / "memory.json"
test_path = Path("pebble_data") / "memory_validation_test.json"

if test_path.exists():
    print("ERROR: The temporary test file already exists.")
    raise SystemExit(1)

try:
    shutil.copy2(source_path, test_path)

    with test_path.open("r", encoding="utf-8") as file:
        original_data = json.load(file)

    test_cases = [
        ("Missing memory", lambda m: m[0]["connections"].append(999)),
        ("One-way connection", lambda m: m[0]["connections"].remove(2)),
        ("Self-connection", lambda m: m[0]["connections"].append(1)),
        ("Duplicate connection", lambda m: m[0]["connections"].append(2)),
        ("Invalid connection ID", lambda m: m[0]["connections"].append("hello")),
    ]

    for test_name, introduce_problem in test_cases:

        test_data = json.loads(json.dumps(original_data))
        introduce_problem(test_data["memories"])

        with test_path.open("w", encoding="utf-8") as file:
            json.dump(test_data, file, indent=4)

        print(f"\n{'=' * 45}")
        print(f"TEST: {test_name}")
        print("=" * 45)

        result = validate_existing_memories(test_path)

        if result is False:
            print(f"PASS: {test_name} was detected.")
        else:
            print(f"FAIL: {test_name} was not detected.")

finally:
    if test_path.exists():
        test_path.unlink()
        print("\nTemporary test file removed.")
