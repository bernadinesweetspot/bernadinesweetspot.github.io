
# --------------------------------------------------
# Pebble's Environment: Environmental Awareness
# --------------------------------------------------

from pebble_environment.locations import get_location_at


class EnvironmentTracker:
    """
    Tracks Pebble's position and recognises known locations.

    This class detects when Pebble enters or leaves
    a recognised location.
    """

    def __init__(self):
        # The location Pebble is currently inside.
        self.current_location = None

    def update_position(self, x, z):
        """
        Update Pebble's position.

        Returns a list of events describing any location
        changes that occurred.
        """

        new_location = get_location_at(x, z)

        events = []

        old_location_id = (
            self.current_location["id"]
            if self.current_location
            else None
        )

        new_location_id = (
            new_location["id"]
            if new_location
            else None
        )

        # Nothing has changed.
        if old_location_id == new_location_id:
            return events

        # Pebble has left its previous location.
        if self.current_location is not None:
            events.append({
                "type": "left_location",
                "location": self.current_location
            })

        # Update Pebble's current location.
        self.current_location = new_location

        # Pebble has entered a new location.
        if self.current_location is not None:
            events.append({
                "type": "entered_location",
                "location": self.current_location
            })

        return events

    def get_current_location(self):
        """
        Return the location Pebble is currently in.

        Returns None if Pebble isn't in a recognised location.
        """

        return self.current_location
