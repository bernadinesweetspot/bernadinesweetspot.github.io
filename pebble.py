import json
from pathlib import Path
from datetime import datetime


def load_json_file(file_path):
    """Load a JSON file and report any problems."""
    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
    except PermissionError:
        print(f"ERROR: Permission denied: {file_path}")
    except OSError as error:
        print(f"ERROR: Could not read {file_path}: {error}")
    except json.JSONDecodeError as error:
        print(f"ERROR: Invalid JSON in {file_path}: {error}")

    return None


def save_json_file(file_path, data):
    """Save information to a JSON file."""
    try:
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"Successfully saved: {file_path.name}")
        return True

    except PermissionError:
        print(f"ERROR: Permission denied: {file_path}")

    except OSError as error:
        print(f"ERROR: Could not save {file_path}: {error}")

    return False


def add_diary_entry(diary_path, entry):
    """Add a new experience to Pebble's diary."""

    # Load the existing diary.
    diary = load_json_file(diary_path)

    # Stop if the diary could not be loaded.
    if diary is None:
        return False

    # Make sure the diary is a list.
    if not isinstance(diary, list):
        print("ERROR: The diary must contain a list.")
        return False

    # Add the new entry without removing previous entries.
    diary.append(entry)

    # Save the updated diary.
    return save_json_file(diary_path, diary)


def validate_memory(content, category):
    """Check whether a new memory contains valid information."""

    # Check that the memory content is text.
    if not isinstance(content, str):
        print("ERROR: Memory content must be text.")
        return False

    # Check that the content isn't empty.
    if not content.strip():
        print("ERROR: Memory content cannot be empty.")
        return False

    # Check that the category is text.
    if not isinstance(category, str):
        print("ERROR: Memory category must be text.")
        return False

    # Normalise the category.
    category = category.strip().lower()

    # Check that the category is recognised.
    valid_categories = [
        "relationship",
        "preference",
        "experience",
        "general"
    ]

    if category not in valid_categories:
        print("ERROR: Invalid memory category.")
        print(f"Choose one of: {', '.join(valid_categories)}")
        return False

    return True



def validate_existing_memories(memory_path):
    """Check the integrity of Pebble's saved memories."""

    # Load the memory file.
    memory_data = load_json_file(memory_path)

    if memory_data is None:
        return False

    # Check the overall structure.
    if not isinstance(memory_data, dict):
        print("ERROR: Memory data must be a dictionary.")
        return False

    memories = memory_data.get("memories")

    if not isinstance(memories, list):
        print("ERROR: The memories collection must be a list.")
        return False

    # Keep track of IDs to detect duplicates.
    seen_ids = set()
    id_counts = {}
    memory_lookup = {}
    invalid_entries = set()

    print("\n--- Checking Existing Memories ---")

    # First pass: check each individual memory.
    for index, memory in enumerate(memories):

        print(f"\nChecking memory entry {index + 1}:")

        if not isinstance(memory, dict):
            print("ERROR: Memory entry must be a dictionary.")
            invalid_entries.add(index)
            continue

        entry_invalid = False

        # Check the memory ID.
        memory_id = memory.get("id")

        if (
            not isinstance(memory_id, int)
            or isinstance(memory_id, bool)
            or memory_id < 1
        ):
            print("ERROR: Memory ID must be a positive integer.")
            entry_invalid = True

        else:
            id_counts[memory_id] = id_counts.get(memory_id, 0) + 1

            if memory_id in seen_ids:
                print(f"ERROR: Duplicate memory ID: {memory_id}.")
                entry_invalid = True
            else:
                seen_ids.add(memory_id)
                memory_lookup[memory_id] = memory

        # Check the content and category.
        if not validate_memory(
            memory.get("content"),
            memory.get("category")
        ):
            entry_invalid = True

        # Check the timestamp.
        created = memory.get("created")

        if not isinstance(created, str):
            print("ERROR: Memory timestamp must be text.")
            entry_invalid = True
        else:
            try:
                datetime.fromisoformat(created)
            except ValueError:
                print("ERROR: Memory timestamp is not a valid ISO date.")
                entry_invalid = True

        if entry_invalid:
            invalid_entries.add(index)
        else:
            print(f"Memory #{memory_id} is valid.")

    # Second pass: check the connections between memories.
    print("\n--- Checking Memory Connections ---")

    for index, memory in enumerate(memories):

        if not isinstance(memory, dict):
            continue

        memory_id = memory.get("id")

        # Skip invalid or duplicate IDs.
        if (
            not isinstance(memory_id, int)
            or isinstance(memory_id, bool)
            or memory_id < 1
            or id_counts.get(memory_id) != 1
        ):
            continue

        connections = memory.get("connections", [])

        # Check that connections are stored in a list.
        if not isinstance(connections, list):
            print(
                f"ERROR: Memory #{memory_id} has an invalid "
                "connections list."
            )
            invalid_entries.add(index)
            continue

        seen_connections = set()

        # Check each individual connection.
        for connected_id in connections:

            if (
                not isinstance(connected_id, int)
                or isinstance(connected_id, bool)
                or connected_id < 1
            ):
                print(
                    f"ERROR: Memory #{memory_id} has an invalid "
                    f"connection ID: {connected_id}."
                )
                invalid_entries.add(index)
                continue

            if connected_id in seen_connections:
                print(
                    f"ERROR: Memory #{memory_id} has a duplicate "
                    f"connection to memory #{connected_id}."
                )
                invalid_entries.add(index)
                continue

            seen_connections.add(connected_id)

            if connected_id == memory_id:
                print(
                    f"ERROR: Memory #{memory_id} is connected to itself."
                )
                invalid_entries.add(index)
                continue

            if connected_id not in memory_lookup:
                print(
                    f"ERROR: Memory #{memory_id} connects to "
                    f"missing or ambiguous memory #{connected_id}."
                )
                invalid_entries.add(index)
                continue

            # Check that the connection also exists in reverse.
            other_memory = memory_lookup[connected_id]
            other_connections = other_memory.get("connections", [])

            if (
                not isinstance(other_connections, list)
                or memory_id not in other_connections
            ):
                print(
                    f"ERROR: Connection between memory #{memory_id} "
                    f"and memory #{connected_id} is not bidirectional."
                )
                invalid_entries.add(index)

    # Display the overall result.
    print("\n--- Validation Results ---")
    print(f"Memories checked: {len(memories)}")
    print(f"Invalid memories: {len(invalid_entries)}")

    if len(invalid_entries) == 0:
        print("All existing memories and connections are valid!")
        return True

    print("Some memories need attention.")
    return False

def update_memory_structure(memory_path):
    """Add new structural fields to older memories."""

    memory_data = load_json_file(memory_path)

    if not isinstance(memory_data, dict):
        print("ERROR: Could not update memory structure.")
        return False

    memories = memory_data.get("memories")

    if not isinstance(memories, list):
        print("ERROR: Memories collection must be a list.")
        return False

    updated_count = 0

    for memory in memories:

        if not isinstance(memory, dict):
            continue

        if "connections" not in memory:
            memory["connections"] = []
            updated_count += 1

    if updated_count > 0:
        if not save_json_file(memory_path, memory_data):
            return False

        print(f"Updated {updated_count} existing memories.")

    else:
        print("All memories already have connection lists.")

    return True


def add_memory(memory_path, content, category="general"):
    """Add a new memory to Pebble's memory collection."""

    # Validate the new memory before saving it.
    if not validate_memory(content, category):
        return False

    # Standardise the category.
    category = category.strip().lower()
    content = content.strip()

    # Load existing memories.
    memory_data = load_json_file(memory_path)

    if memory_data is None:
        return False

    # Check that the memory collection exists.
    if not isinstance(memory_data, dict):
        print("ERROR: Memory data must be a dictionary.")
        return False

    if "memories" not in memory_data:
        memory_data["memories"] = []

    memories = memory_data["memories"]

    if not isinstance(memories, list):
        print("ERROR: The memories collection must be a list.")
        return False

    # Generate a unique ID for the new memory.
    if memories:
        new_id = max(
            memory.get("id", 0)
            for memory in memories
        ) + 1
    else:
        new_id = 1

    # Create the new memory.
    new_memory = {
        "id": new_id,
        "content": content,
        "category": category,
        "created": datetime.now().astimezone().isoformat(),
        "connections": []
    }

    # Add the memory and save the collection.
    memories.append(new_memory)
    memory_data["memories"] = memories

    return save_json_file(memory_path, memory_data)


def get_memories(memory_path, category=None):
    """Retrieve Pebble's memories, optionally filtering by category."""

    # Load the existing memory data.
    memory_data = load_json_file(memory_path)

    if memory_data is None:
        return []

    # Check that the memory data has the correct structure.
    if not isinstance(memory_data, dict):
        print("ERROR: Memory data must be a dictionary.")
        return []

    memories = memory_data.get("memories", [])

    if not isinstance(memories, list):
        print("ERROR: The memories collection must be a list.")
        return []

    # Return all memories if no category was specified.
    if category is None:
        return memories

    # Otherwise, return only memories in the requested category.
    return [
        memory for memory in memories
        if isinstance(memory, dict)
        and memory.get("category", "").lower() == category.lower()
    ]


def connect_memories(memory_path, first_memory_id, second_memory_id):
    """Create a two-way connection between two memories."""

    # Check that both IDs are positive integers.
    if (
        not isinstance(first_memory_id, int)
        or isinstance(first_memory_id, bool)
        or first_memory_id < 1
        or not isinstance(second_memory_id, int)
        or isinstance(second_memory_id, bool)
        or second_memory_id < 1
    ):
        print("ERROR: Memory IDs must be positive integers.")
        return False

    # A memory cannot be connected to itself.
    if first_memory_id == second_memory_id:
        print("ERROR: A memory cannot be connected to itself.")
        return False

    # Load the memory collection.
    memory_data = load_json_file(memory_path)

    if not isinstance(memory_data, dict):
        return False

    memories = memory_data.get("memories")

    if not isinstance(memories, list):
        return False

    # Find both memories.
    first_memory = None
    second_memory = None

    for memory in memories:

        if not isinstance(memory, dict):
            continue

        if memory.get("id") == first_memory_id:
            first_memory = memory

        if memory.get("id") == second_memory_id:
            second_memory = memory

    # Make sure both memories exist.
    if first_memory is None or second_memory is None:
        print("ERROR: Could not find both memories.")
        return False

    # Check that both memories have valid connection lists.
    if not isinstance(first_memory.get("connections"), list):
        print("ERROR: First memory has an invalid connections list.")
        return False

    if not isinstance(second_memory.get("connections"), list):
        print("ERROR: Second memory has an invalid connections list.")
        return False

    # Add the connection in both directions.
    if second_memory_id not in first_memory["connections"]:
        first_memory["connections"].append(second_memory_id)

    if first_memory_id not in second_memory["connections"]:
        second_memory["connections"].append(first_memory_id)

    # Save the updated memories.
    if save_json_file(memory_path, memory_data):
        print(
            f"Connected memory #{first_memory_id} "
            f"with memory #{second_memory_id}."
        )
        return True

    return False


def get_connected_memories(memory_path, memory_id):
    """Retrieve all memories connected to a specific memory."""

    # Check that the requested ID is valid.
    if (
        not isinstance(memory_id, int)
        or isinstance(memory_id, bool)
        or memory_id < 1
    ):
        print("ERROR: Memory ID must be a positive integer.")
        return []

    # Load the memory collection.
    memory_data = load_json_file(memory_path)

    if not isinstance(memory_data, dict):
        return []

    memories = memory_data.get("memories")

    if not isinstance(memories, list):
        return []

    # Find the requested memory.
    target_memory = None

    for memory in memories:

        if isinstance(memory, dict) and memory.get("id") == memory_id:
            target_memory = memory
            break

    if target_memory is None:
        print(f"ERROR: Memory #{memory_id} could not be found.")
        return []

    # Get the IDs of its connected memories.
    connections = target_memory.get("connections", [])

    if not isinstance(connections, list):
        print("ERROR: Memory has an invalid connections list.")
        return []

    # Find the connected memories.
    connected_memories = []

    for connected_id in connections:

        for memory in memories:

            if not isinstance(memory, dict):
                continue

            if memory.get("id") == connected_id:
                connected_memories.append(memory)
                break

    return connected_memories


def get_related_memories(memory_path, memory_id, max_depth=2):
    """Retrieve memories connected directly or indirectly."""

    # Validate the starting ID.
    if (
        not isinstance(memory_id, int)
        or isinstance(memory_id, bool)
        or memory_id < 1
    ):
        print("ERROR: Memory ID must be a positive integer.")
        return []

    # Validate the search depth.
    if (
        not isinstance(max_depth, int)
        or isinstance(max_depth, bool)
        or max_depth < 1
    ):
        print("ERROR: Search depth must be a positive integer.")
        return []

    # Load the memory collection.
    memory_data = load_json_file(memory_path)

    if not isinstance(memory_data, dict):
        return []

    memories = memory_data.get("memories")

    if not isinstance(memories, list):
        return []

    # Build a lookup of memories by ID.
    memory_lookup = {}

    for memory in memories:

        if not isinstance(memory, dict):
            continue

        saved_id = memory.get("id")

        if (
            isinstance(saved_id, int)
            and not isinstance(saved_id, bool)
            and saved_id > 0
        ):
            memory_lookup[saved_id] = memory

    # Check that the starting memory exists.
    if memory_id not in memory_lookup:
        print(f"ERROR: Memory #{memory_id} could not be found.")
        return []

    # Prepare the search.
    visited_ids = {memory_id}
    queue = [(memory_id, 0)]
    related_memories = []

    # Explore connected memories.
    while queue:

        current_id, current_depth = queue.pop(0)

        if current_depth >= max_depth:
            continue

        current_memory = memory_lookup[current_id]
        connections = current_memory.get("connections", [])

        if not isinstance(connections, list):
            continue

        for connected_id in connections:

            # Ignore invalid IDs and already visited memories.
            if (
                not isinstance(connected_id, int)
                or isinstance(connected_id, bool)
                or connected_id < 1
                or connected_id in visited_ids
            ):
                continue

            # Ignore connections to missing memories.
            if connected_id not in memory_lookup:
                continue

            # Mark this memory as visited.
            visited_ids.add(connected_id)

            # Add this memory to the results.
            connected_memory = memory_lookup[connected_id]

            # Make a copy so we don't change the saved memory.
            related_memory = connected_memory.copy()

            # Record how many connections away this memory was found.
            related_memory["connection_depth"] = current_depth + 1

            related_memories.append(related_memory)

            # Add it to the search queue.
            queue.append((connected_id, current_depth + 1))

    return related_memories


def search_memories(memory_path, keyword):
    """Search Pebble's memories for a word or phrase."""

    # Retrieve all existing memories.
    memories = get_memories(memory_path)

    # Remove unnecessary spaces from the search.
    keyword = keyword.strip().lower()

    # Don't search if the keyword is empty.
    if not keyword:
        print("Please enter a search term.")
        return []

    # Find memories containing the keyword.
    results = [
        memory for memory in memories
        if keyword in memory.get("content", "").lower()
    ]

    return results



def delete_memory(memory_path, memory_id):
    """Delete one of Pebble's memories using its ID."""

    # Load existing memory data.
    memory_data = load_json_file(memory_path)

    if memory_data is None:
        return False

    # Check the memory data structure.
    if not isinstance(memory_data, dict):
        print("ERROR: Memory data must be a dictionary.")
        return False

    memories = memory_data.get("memories", [])

    if not isinstance(memories, list):
        print("ERROR: The memories collection must be a list.")
        return False

    # Find the memory with the requested ID.
    for index, memory in enumerate(memories):

        if isinstance(memory, dict) and memory.get("id") == memory_id:

            # Remove connections to this memory from other memories.
            for other_memory in memories:

                if not isinstance(other_memory, dict):
                    continue

                connections = other_memory.get("connections", [])

                if isinstance(connections, list):
                    other_memory["connections"] = [
                        connected_id
                        for connected_id in connections
                        if connected_id != memory_id
                    ]

            # Remove only the matching memory.
            deleted_memory = memories.pop(index)

            # Save the updated collection.
            if save_json_file(memory_path, memory_data):
                print(
                    f"Deleted memory #{memory_id}: "
                    f"{deleted_memory.get('content', '')}"
                )
                return True

            return False

    print(f"No memory found with ID {memory_id}.")
    return False


def get_memory_by_id(memory_path, memory_id):
    """Retrieve one of Pebble's memories using its ID."""

    # Load all existing memories.
    memories = get_memories(memory_path)

    # Look for the requested memory.
    for memory in memories:
        if isinstance(memory, dict) and memory.get("id") == memory_id:
            return memory

    # Return None if no matching memory exists.
    return None


def main():
    # Find the folder containing this Python script.
    project_folder = Path(__file__).resolve().parent

    # Find Pebble's data folder.
    data_folder = project_folder / "pebble_data"

    print("=" * 33)
    print("       Welcome to Pebble!")
    print("=" * 33)

    # Load Pebble's three data files.
    memory = load_json_file(data_folder / "memory.json")
    diary = load_json_file(data_folder / "diary.json")
    state = load_json_file(data_folder / "state.json")

    # Stop if any data could not be loaded.
    if memory is None or diary is None or state is None:
        print("\nPebble could not load all its data.")
        return

    # Check that each file contains the expected kind of data.
    if not isinstance(memory, dict):
        print("ERROR: memory.json must contain an object.")
        return

    if not isinstance(diary, list):
        print("ERROR: diary.json must contain a list.")
        return

    if not isinstance(state, dict):
        print("ERROR: state.json must contain an object.")
        return


    # Check the integrity of existing memories.
    if not validate_existing_memories(data_folder / "memory.json"):
        print("\nPebble's memory data needs attention.")
        print("Stopping to prevent further changes.")
        return

    # Update older memories with the latest structure.
    update_memory_structure(data_folder / "memory.json")

    # Ask whether to give Pebble a new memory.
    remember = input("\nWould you like Pebble to remember something? (y/n): ")


    if remember.lower() == "y":
        content = input("What should Pebble remember? ")
        category = input("Memory category (relationship/preference/experience/general): ")

        add_memory(
            data_folder / "memory.json",
            content,
            category
        )

        # Reload memories to update the displayed count.
        memory = load_json_file(data_folder / "memory.json")


    # Ask whether to record a new diary entry.
    answer = input("\nWould you like to add a diary entry? (y/n): ")

    if answer.lower() == "y":
        experience = input("What happened? ")

        if experience.strip():
            new_entry = {
                "experience": experience,
                "timestamp": datetime.now().astimezone().isoformat(),
                "type": "user_recorded"
            }

            add_diary_entry(data_folder / "diary.json", new_entry)

            # Reload the diary so the count is up to date.
            diary = load_json_file(data_folder / "diary.json")


    # Test retrieving Pebble's memories.
    print("\n--- Pebble's Memories ---")

    memories = get_memories(data_folder / "memory.json")

    if memories:
        for memory in memories:
            print(f"\nMemory #{memory['id']}")
            print(f"Category: {memory['category']}")
            print(f"Remembered: {memory['content']}")
            print(f"Created: {memory['created']}")
    else:
        print("Pebble doesn't have any memories yet.")


    # Ask whether to search Pebble's memories.
    search_answer = input("\nWould you like to search Pebble's memories? (y/n): ")

    if search_answer.lower() == "y":
        keyword = input("What would you like to search for? ")

        results = search_memories(
            data_folder / "memory.json",
            keyword
        )

        if results:
            print(f"\nFound {len(results)} matching memories:")

            for memory in results:
                print(f"\nMemory #{memory['id']}")
                print(f"Category: {memory['category']}")
                print(f"Remembered: {memory['content']}")
        else:
            print("\nNo matching memories found.")


    # Ask whether to delete a memory.
    delete_answer = input("\nWould you like to delete a memory? (y/n): ")

    if delete_answer.lower() == "y":
        memory_id_input = input("Enter the ID of the memory to delete: ")

        try:
            memory_id = int(memory_id_input)

            # Show the memory before asking for confirmation.
            memories = get_memories(data_folder / "memory.json")

            selected_memory = next(
                (
                    memory for memory in memories
                    if memory.get("id") == memory_id
                ),
                None
            )

            if selected_memory:
                print(f"\nSelected memory: {selected_memory['content']}")

                confirm = input("Are you sure you want to delete it? (y/n): ")

                if confirm.lower() == "y":
                    delete_memory(
                        data_folder / "memory.json",
                        memory_id
                    )
                else:
                    print("Memory deletion cancelled.")

            else:
                print(f"No memory found with ID {memory_id}.")

        except ValueError:
            print("Please enter a valid numeric memory ID.")


    # Test retrieving one memory by ID.
    lookup_answer = input("\nWould you like to look up a memory by ID? (y/n): ")

    if lookup_answer.lower() == "y":
        memory_id_input = input("Which memory ID would you like to retrieve? ")

        try:
            memory_id = int(memory_id_input)

            selected_memory = get_memory_by_id(
                data_folder / "memory.json",
                memory_id
            )

            if selected_memory:
                print("\n--- Retrieved Memory ---")
                print(f"ID: {selected_memory['id']}")
                print(f"Category: {selected_memory['category']}")
                print(f"Remembered: {selected_memory['content']}")
                print(f"Created: {selected_memory['created']}")
            else:
                print(f"No memory found with ID {memory_id}.")

        except ValueError:
            print("Please enter a valid numeric memory ID.")


    # Ask whether to connect two memories.
    connect_answer = input(
        "\nWould you like to connect two memories? (y/n): "
    )

    if connect_answer.lower() == "y":

        try:
            first_memory_id = int(
                input("Enter the first memory ID: ")
            )

            second_memory_id = int(
                input("Enter the second memory ID: ")
            )

        except ValueError:
            print("ERROR: Please enter valid whole-number memory IDs.")

        else:
            connect_memories(
                data_folder / "memory.json",
                first_memory_id,
                second_memory_id
            )



    # Ask whether to explore memories connected to another memory.
    explore_answer = input(
        "\nWould you like to explore related memories? (y/n): "
    )

    if explore_answer.lower() == "y":

        try:
            starting_memory_id = int(
                input("Which memory would you like to explore? Enter its ID: ")
            )

            max_depth = int(
                input("How many connection levels should Pebble explore? ")
            )

        except ValueError:
            print("ERROR: Please enter valid whole numbers.")

        else:
            # Find the memory Pebble will start with.
            starting_memory = get_memory_by_id(
                data_folder / "memory.json",
                starting_memory_id
            )

            if starting_memory is None:
                print(f"\nMemory #{starting_memory_id} does not exist.")

            elif max_depth < 1:
                print("\nERROR: Connection depth must be at least 1.")

            else:
                # Retrieve memories connected to the starting memory.
                related_memories = get_related_memories(
                    data_folder / "memory.json",
                    starting_memory_id,
                    max_depth
                )

                print("\n--- Memory Exploration ---")
                print("\nStarting Memory:")
                print(f"Memory #{starting_memory['id']}")
                print(f"Remembered: {starting_memory['content']}")

                if related_memories:
                    print("\n--- Related Memories ---")

                    for memory in related_memories:
                        print(f"\nMemory #{memory['id']}")
                        print(f"Category: {memory['category']}")
                        print(f"Remembered: {memory['content']}")
                        print(f"Connections: {memory['connections']}")
                        print(
                            f"Distance: {memory['connection_depth']} "
                            "connection(s) away"
                        )

                else:
                    print("\nThis memory has no related memories.")



    # Display Pebble's current information.
    print(f"\nName: {state.get('name', 'Unknown')}")
    print(f"Status: {state.get('status', 'Unknown')}")
    print(f"\nMemories recorded: {len(get_memories(data_folder / 'memory.json'))}")
    print(f"Diary entries: {len(diary)}")

    print("\nPebble's data loaded successfully!")
    print("=" * 33)


if __name__ == "__main__":
    main()
