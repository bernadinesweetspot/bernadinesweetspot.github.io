
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_ROOT / "pebble_data"
STATE_FILE = DATA_FOLDER / "state.json"


# --------------------------------------------------
# ACTIVITY SETTINGS
# --------------------------------------------------

ACTIVITIES = [
    "explore",
    "rest",
    "play",
    "reflect",
]

# Short durations for the first test.
# We can make these longer later.
MIN_ACTIVITY_SECONDS = 10
MAX_ACTIVITY_SECONDS = 20


# --------------------------------------------------
# TIME AND DATA HELPERS
# --------------------------------------------------

def current_time():
    return datetime.now().astimezone()


def timestamp():
    return current_time().isoformat(timespec="seconds")


def load_state():
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE.exists():
        return {
            "name": "Pebble",
            "status": "not_started",
            "current_activity": None,
            "last_activity": None,
            "created": None,
            "last_updated": None,
        }

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    state["last_updated"] = timestamp()

    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


# --------------------------------------------------
# ACTIVITY SELECTION
# --------------------------------------------------

def choose_activity(previous_activity):
    available_activities = [
        activity
        for activity in ACTIVITIES
        if activity != previous_activity
    ]

    return random.choice(available_activities)


# --------------------------------------------------
# AUTONOMOUS ACTIVITY LOOP
# --------------------------------------------------

def run_pebble():
    state = load_state()

    if state.get("created") is None:
        state["created"] = timestamp()

    state["status"] = "running"
    save_state(state)

    print(f"{state.get('name', 'Pebble')} is now awake.")
    print("Pebble will choose activities independently.")
    print("Press CTRL+C to stop Pebble.\n")

    try:
        while True:
            previous_activity = state.get("last_activity")
            activity = choose_activity(previous_activity)

            duration = random.randint(
                MIN_ACTIVITY_SECONDS,
                MAX_ACTIVITY_SECONDS,
            )

            started = current_time()
            finishes = started + timedelta(seconds=duration)

            state["current_activity"] = activity
            state["activity_started"] = started.isoformat(
                timespec="seconds"
            )
            state["activity_ends"] = finishes.isoformat(
                timespec="seconds"
            )

            save_state(state)

            print(f"Pebble decided to: {activity}")
            print(f"Pebble will spend {duration} seconds doing this.")

            time.sleep(duration)

            # The activity has finished.
            state["last_activity"] = activity
            state["current_activity"] = None
            state.pop("activity_started", None)
            state.pop("activity_ends", None)

            save_state(state)

            print(f"Pebble finished: {activity}\n")

    except KeyboardInterrupt:
        print("\nStopping Pebble...")

        state["status"] = "stopped"
        state["current_activity"] = None
        state.pop("activity_started", None)
        state.pop("activity_ends", None)

        save_state(state)

        print("Pebble has stopped safely.")


if __name__ == "__main__":
    run_pebble()
