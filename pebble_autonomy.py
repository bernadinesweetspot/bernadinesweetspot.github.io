import json
import random
import threading
import time

from pebble_decisions import choose_activity
from pebble_reflection import reflect
from pebble_environment.location_memory import (
    load_location_memories,
    update_location_memory,
    record_location_activity,
)

from pebble_environment.locations import LOCATIONS
from pebble_environment.environment import EnvironmentTracker

from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FOLDER = PROJECT_ROOT / "pebble_data"
STATE_FILE = DATA_FOLDER / "state.json"
DIARY_FILE = DATA_FOLDER / "diary.json"

# --------------------------------------------------
# ACTIVITY SETTINGS
# --------------------------------------------------

ACTIVITIES = ["explore", "rest", "play", "reflect"]

MIN_ACTIVITY_SECONDS = 10
MAX_ACTIVITY_SECONDS = 20

# Maximum time Pebble will wait for an exploration.
EXPLORATION_TIMEOUT = 60

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 8765


# --------------------------------------------------
# SHARED COMMUNICATION
# --------------------------------------------------

pending_command = None
command_lock = threading.Lock()
exploration_finished = threading.Event()


# --------------------------------------------------
# TIME AND STATE HELPERS
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



def record_activity(activity, location=None):
    # Load Pebble's existing diary.
    if DIARY_FILE.exists():
        with DIARY_FILE.open("r", encoding="utf-8") as file:
            diary = json.load(file)
    else:
        diary = []

    # Describe what Pebble actually completed.
    descriptions = {
        "explore": "Pebble finished exploring.",
        "rest": "Pebble spent time resting.",
        "play": "Pebble spent time playing.",
        "reflect": "Pebble spent time reflecting.",
    }

    entry = {
        "experience": descriptions[activity],
        "type": "activity",
        "timestamp": timestamp(),
    }

    # Record the location if Pebble is somewhere recognised.
    if location is not None:
        entry["location_id"] = location["id"]
        entry["location_name"] = location["name"]

    diary.append(entry)

    # Save the updated diary.
    with DIARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(diary, file, indent=4)

    print(f"Pebble recorded a diary entry: {entry['experience']}")

    if location is not None:
        print(f"Location recorded: {location['name']}")

        # Record the completed activity at this location.
        record_location_activity(location, activity)


def record_location_visit(location):
    """Record Pebble's visit to a recognised location."""

    # Load Pebble's existing diary.
    if DIARY_FILE.exists():
        with DIARY_FILE.open("r", encoding="utf-8") as file:
            diary = json.load(file)
    else:
        diary = []

    # Describe the location Pebble visited.
    entry = {
        "experience": f"Pebble visited {location['name']}.",
        "type": "location_visit",
        "location_id": location["id"],
        "location_name": location["name"],
        "timestamp": timestamp(),
    }

    diary.append(entry)

    # Save the updated diary.
    with DIARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(diary, file, indent=4)

    print(f"Pebble recorded a location visit: {location['name']}")
    update_location_memory(location)


# --------------------------------------------------
# HTTP CONNECTION TO THREE.JS
# --------------------------------------------------

class PebbleRequestHandler(BaseHTTPRequestHandler):

    def send_json(self, data):
        response = json.dumps(data).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        global pending_command

        if self.path != "/api/command":
            self.send_json({"error": "Unknown endpoint"})
            return

        with command_lock:
            command = pending_command
            pending_command = None

        self.send_json({"command": command})

    def do_POST(self):
        if self.path != "/api/arrived":
            self.send_json({"error": "Unknown endpoint"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(content_length)

        exploration_finished.set()

        self.send_json({"received": True})

    def log_message(self, format, *args):
        # Keep routine browser polling out of the console.
        pass


def start_server():
    server = ThreadingHTTPServer(
        (SERVER_ADDRESS, SERVER_PORT),
        PebbleRequestHandler,
    )

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    server_thread.start()

    print(f"Python connection ready at http://{SERVER_ADDRESS}:{SERVER_PORT}")

    return server


# --------------------------------------------------
# EXPLORATION
# --------------------------------------------------


def explore(state, environment_tracker):
    global pending_command

    # --------------------------------------------------
    # Choose an exploration destination
    # --------------------------------------------------

    memories = load_location_memories()

    current_location = environment_tracker.get_current_location()

    current_location_id = (
        current_location["id"]
        if current_location
        else None
    )

    if memories is None:
        # If location memories cannot be read, explore randomly.
        print("Pebble couldn't access its location memories.")
        destination_x = round(random.uniform(-12, 12), 2)
        destination_z = round(random.uniform(-12, 12), 2)

    else:
        # Separate recognised places into visited and unvisited.
        unvisited_locations = [
            location
            for location in LOCATIONS.values()
            if location["id"] not in memories
            and location["id"] != current_location_id
        ]

        visited_locations = [
            location
            for location in LOCATIONS.values()
            if location["id"] in memories
            and location["id"] != current_location_id
        ]

        chosen_location = None

        # Prefer discovering somewhere new.
        if unvisited_locations and random.random() < 0.7:
            chosen_location = random.choice(unvisited_locations)

        # Once places are familiar, sometimes revisit them.
        elif visited_locations and random.random() < 0.6:
            chosen_location = random.choice(visited_locations)

        if chosen_location:
            destination_x = chosen_location["x"]
            destination_z = chosen_location["z"]

            print(
                f"Pebble chose to explore "
                f"{chosen_location['name']}."
            )

        else:
            # Explore an otherwise random part of the environment.
            destination_x = round(random.uniform(-12, 12), 2)
            destination_z = round(random.uniform(-12, 12), 2)

            print("Pebble chose to explore somewhere freely.")

    # --------------------------------------------------
    # Send the destination to Three.js
    # --------------------------------------------------

    command = {
        "type": "move_to",
        "x": destination_x,
        "z": destination_z,
    }

    exploration_finished.clear()

    with command_lock:
        pending_command = command

    print(
        f"Pebble is exploring towards "
        f"({destination_x}, {destination_z})."
    )

    # Wait for Pebble to reach the destination.
    finished = exploration_finished.wait(
        timeout=EXPLORATION_TIMEOUT
    )

    if finished:
        print("Pebble arrived at their destination.")

        # Check whether Pebble entered or left a known location.
        events = environment_tracker.update_position(
            destination_x,
            destination_z
        )

        for event in events:

            if event["type"] == "entered_location":
                location = event["location"]

                print(
                    f"Pebble discovered they are at "
                    f"{location['name']}."
                )

                record_location_visit(location)

            elif event["type"] == "left_location":
                location = event["location"]

                print(
                    f"Pebble left {location['name']}."
                )

        return True

    print("Pebble's exploration timed out.")
    return False


# --------------------------------------------------
# OTHER ACTIVITIES
# --------------------------------------------------

def perform_activity(activity, duration):
    if activity == "explore":
        return None

    global pending_command

    # Tell Three.js which activity animation to play.
    with command_lock:
        pending_command = {
            "type": "activity",
            "activity": activity,
        }

    print(f"Pebble is spending time doing: {activity}")

    # Let the activity continue for its chosen duration.
    time.sleep(duration)

    # Tell Three.js to return to idle.
    with command_lock:
        pending_command = {
            "type": "activity",
            "activity": "idle",
        }

    print(f"Pebble finished: {activity}")
    return True


# --------------------------------------------------
# AUTONOMOUS LOOP
# --------------------------------------------------

def run_pebble():
    global pending_command
    state = load_state()

    if state.get("created") is None:
        state["created"] = timestamp()

    state["status"] = "running"
    save_state(state)

    server = start_server()

    environment_tracker = EnvironmentTracker()

    print("\nPebble is now autonomous.")
    print("Open the 3D environment in your browser.")
    print("Press CTRL+C to stop Pebble.\n")

    try:
        while True:
            previous_activity = state.get("last_activity")
            activity = choose_activity(previous_activity)

            duration = random.randint(
                MIN_ACTIVITY_SECONDS,
                MAX_ACTIVITY_SECONDS,
            )

            state["current_activity"] = activity

            started = current_time()
            state["activity_started"] = started.isoformat(
                timespec="seconds"
            )

            state["activity_ends"] = (
                started + timedelta(seconds=duration)
            ).isoformat(timespec="seconds")

            save_state(state)

            print(f"\nPebble decided to: {activity}")

            if activity == "explore":
                completed = explore(state, environment_tracker)
            else:
                completed = perform_activity(activity, duration)

            if completed is True:
                state["last_activity"] = activity

                # Record the activity and Pebble's current location.
                current_location = environment_tracker.get_current_location()
                record_activity(activity, current_location)

                reflect()

            state["current_activity"] = None
            state.pop("activity_started", None)
            state.pop("activity_ends", None)

            save_state(state)

    except KeyboardInterrupt:
        print("\nStopping Pebble...")

    finally:
        with command_lock:
            pending_command = None

        state["status"] = "stopped"
        state["current_activity"] = None
        state.pop("activity_started", None)
        state.pop("activity_ends", None)

        save_state(state)

        server.shutdown()
        server.server_close()

        print("Pebble has stopped safely.")


if __name__ == "__main__":
    run_pebble()
