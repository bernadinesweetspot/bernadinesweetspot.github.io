
import json

from collections import Counter
from datetime import datetime
from pathlib import Path

from pebble import add_memory, get_memories


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_ROOT / "pebble_data"

DIARY_FILE = DATA_FOLDER / "diary.json"
THOUGHTS_FILE = DATA_FOLDER / "thoughts.json"
MEMORY_FILE = DATA_FOLDER / "memory.json"


# --------------------------------------------------
# ACTIVITY DESCRIPTIONS
# --------------------------------------------------

ACTIVITY_DESCRIPTIONS = {
    "Pebble finished exploring.": "explore",
    "Pebble spent time resting.": "rest",
    "Pebble spent time playing.": "play",
    "Pebble spent time reflecting.": "reflect",
}

THOUGHTS = {
    "explore": (
        "I've been exploring quite a bit lately. "
        "I wonder what else I might discover."
    ),
    "rest": (
        "I've been spending quite a bit of time resting lately."
    ),
    "play": (
        "I've been playing quite a bit lately. "
        "I wonder what else I could do?"
    ),
    "reflect": (
        "I've been spending time thinking about things lately."
    ),
}


# --------------------------------------------------
# TIME AND FILE HELPERS
# --------------------------------------------------

def timestamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json_list(file_path):
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{file_path.name} must contain a JSON list.")

    return data


# --------------------------------------------------
# THOUGHT STORAGE
# --------------------------------------------------


def save_thought(thought, focus_activity=None):
    thoughts = load_json_list(THOUGHTS_FILE)

    # Avoid saving the exact same thought repeatedly.
    if (
        thoughts
        and thoughts[-1].get("thought") == thought
        and thoughts[-1].get("focus_activity") == focus_activity
    ):
        return

    entry = {
        "thought": thought,
        "type": "reflection",
        "focus_activity": focus_activity,
        "timestamp": timestamp(),
    }

    thoughts.append(entry)

    with THOUGHTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(thoughts, file, indent=4)

    print(f"\nPebble thought: {thought}")


# --------------------------------------------------
# LONG-TERM MEMORY
# --------------------------------------------------

def save_reflection_memory(activity):
    memory_content = (
        f"Pebble has repeatedly chosen to {activity} "
        f"in its recent activities."
    )

    existing_memories = get_memories(MEMORY_FILE)

    # Do not create the same memory more than once.
    for memory in existing_memories:
        if memory.get("content") == memory_content:
            return

    add_memory(
        MEMORY_FILE,
        memory_content,
        category="experience",
    )

    print(f"Pebble formed a memory: {memory_content}")


# --------------------------------------------------
# REFLECTION
# --------------------------------------------------

def reflect():
    diary = load_json_list(DIARY_FILE)

    # Only consider activities Pebble actually completed.
    activities = [
        ACTIVITY_DESCRIPTIONS[entry["experience"]]
        for entry in diary
        if entry.get("type") == "activity"
        and entry.get("experience") in ACTIVITY_DESCRIPTIONS
    ]

    # Wait until Pebble has at least three activities.
    # Only reflect every three completed activities.
    if len(activities) < 3 or len(activities) % 3 != 0:
        return

    recent_activities = activities[-5:]

    activity_counts = Counter(recent_activities)

    most_common_activity, count = activity_counts.most_common(1)[0]

    # Form a thought based on the recent activity pattern.
    if count >= 2:
        thought = THOUGHTS[most_common_activity]
    else:
        thought = (
            "I've been trying a few different activities lately."
        )

    save_thought(
        thought,
        focus_activity=most_common_activity if count >= 2 else None,
    )

    # Only form a permanent memory when a pattern is repeated
    # at least three times in the five most recent activities.
    if count >= 3:
        save_reflection_memory(most_common_activity)
