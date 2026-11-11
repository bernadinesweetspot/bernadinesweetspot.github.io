
import json
from pathlib import Path
from datetime import datetime


# Find locations.json in this same folder.
LOCATION_MEMORY_FILE = (
    Path(__file__).resolve().parent / "locations.json"
)


def load_location_memories():
    """Load Pebble's saved knowledge of recognised locations."""

    if not LOCATION_MEMORY_FILE.exists():
        return {}

    try:
        with LOCATION_MEMORY_FILE.open("r", encoding="utf-8") as file:
            memories = json.load(file)

    except json.JSONDecodeError as error:
        print(f"ERROR: locations.json contains invalid JSON: {error}")
        return None

    except OSError as error:
        print(f"ERROR: Could not read locations.json: {error}")
        return None

    if not isinstance(memories, dict):
        print("ERROR: Location memories must be stored as an object.")
        return None

    return memories


def save_location_memories(memories):
    """Save Pebble's location memories."""

    try:
        with LOCATION_MEMORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(memories, file, indent=4, ensure_ascii=False)

        return True

    except OSError as error:
        print(f"ERROR: Could not save locations.json: {error}")
        return False


def update_location_memory(location):
    """Record a visit to a recognised location."""

    # Check that the location has the information we need.
    if not isinstance(location, dict):
        print("ERROR: Location information must be a dictionary.")
        return False

    location_id = location.get("id")
    location_name = location.get("name")

    if not isinstance(location_id, str) or not location_id.strip():
        print("ERROR: Location is missing a valid ID.")
        return False

    if not isinstance(location_name, str) or not location_name.strip():
        print("ERROR: Location is missing a valid name.")
        return False

    # Load existing location memories.
    memories = load_location_memories()

    if memories is None:
        return False

    # Record the current time.
    visit_time = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    # Check whether Pebble has visited this location before.
    if location_id not in memories:

        # Create a new record for a first visit.
        memories[location_id] = {
            "location_name": location_name,
            "visits": 0,
            "first_visited": visit_time,
            "last_visited": visit_time
        }

    location_memory = memories[location_id]

    # Check that the existing record has the expected structure.
    if not isinstance(location_memory, dict):
        print(
            f"ERROR: Location memory for {location_id} "
            "has an invalid structure."
        )
        return False

    # Keep the location name up to date.
    location_memory["location_name"] = location_name

    # Increase the visit count.
    visits = location_memory.get("visits", 0)

    if (
        not isinstance(visits, int)
        or isinstance(visits, bool)
        or visits < 0
    ):
        print(
            f"ERROR: Invalid visit count for {location_name}."
        )
        return False

    location_memory["visits"] = visits + 1

    # Preserve the original first visit date.
    if not location_memory.get("first_visited"):
        location_memory["first_visited"] = visit_time

    # Update the most recent visit date.
    location_memory["last_visited"] = visit_time

    # Save the updated information.
    if save_location_memories(memories):
        print(
            f"Pebble remembers visiting {location_name}."
        )
        print(
            f"Total visits: {location_memory['visits']}"
        )
        return True

    return False


def get_location_memory(location_id):
    """Retrieve Pebble's experience of one location."""

    memories = load_location_memories()

    if memories is None:
        return None

    return memories.get(location_id)
