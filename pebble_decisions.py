
import json
import random

from collections import Counter
from pathlib import Path

from pebble import get_memories


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_ROOT / "pebble_data"

THOUGHTS_FILE = DATA_FOLDER / "thoughts.json"
MEMORY_FILE = DATA_FOLDER / "memory.json"


# --------------------------------------------------
# AVAILABLE ACTIVITIES
# --------------------------------------------------

ACTIVITIES = ["explore", "rest", "play", "reflect"]


# --------------------------------------------------
# FILE HELPERS
# --------------------------------------------------

def load_thoughts():
    if not THOUGHTS_FILE.exists():
        return []

    with THOUGHTS_FILE.open("r", encoding="utf-8") as file:
        thoughts = json.load(file)

    if not isinstance(thoughts, list):
        raise ValueError("thoughts.json must contain a list.")

    return thoughts


# --------------------------------------------------
# READ RECENT THOUGHTS
# --------------------------------------------------

def get_latest_thought_activity():
    thoughts = load_thoughts()

    if not thoughts:
        return None

    latest_thought = thoughts[-1]

    activity = latest_thought.get("focus_activity")

    if activity in ACTIVITIES:
        return activity

    return None


# --------------------------------------------------
# READ LONG-TERM MEMORIES
# --------------------------------------------------

def get_memory_activity_patterns():
    memories = get_memories(MEMORY_FILE)

    activity_counts = Counter()

    prefix = "Pebble has repeatedly chosen to "
    suffix = " in its recent activities."

    for memory in memories:
        content = memory.get("content", "")

        if not content.startswith(prefix):
            continue

        if not content.endswith(suffix):
            continue

        activity = content[len(prefix):-len(suffix)]

        if activity in ACTIVITIES:
            activity_counts[activity] += 1

    return activity_counts


# --------------------------------------------------
# ACTIVITY DECISIONS
# --------------------------------------------------

def choose_activity(previous_activity=None):

    # Start every activity with an equal score.
    scores = {
        activity: 3
        for activity in ACTIVITIES
    }

    # Avoid immediately repeating the previous activity.
    available = [
        activity
        for activity in ACTIVITIES
        if activity != previous_activity
    ]

    # Read Pebble's latest reflection.
    thought_activity = get_latest_thought_activity()

    if thought_activity:
        scores[thought_activity] -= 1

    # Read Pebble's long-term activity memories.
    memory_patterns = get_memory_activity_patterns()

    for activity, count in memory_patterns.items():
        scores[activity] -= min(count, 2)

    # Never allow an activity to have zero probability.
    weights = [
        max(1, scores[activity])
        for activity in available
    ]

    print("\nPebble considered its thoughts and memories.")

    for activity in available:
        print(
            f"  {activity}: "
            f"score {scores[activity]}"
        )

    # Choose randomly, using the calculated scores.
    decision = random.choices(
        available,
        weights=weights,
        k=1,
    )[0]

    print(f"Pebble decided to: {decision}")

    return decision
