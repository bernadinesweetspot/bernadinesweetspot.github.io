
# --------------------------------------------------
# Pebble's Environment: Known Locations
# --------------------------------------------------
#
# This file defines places Pebble can recognise.
#
# Each location has:
# - A unique ID
# - A display name
# - A description
# - A location type
# - A centre position (x, z)
# - An elliptical recognition area
#
# Coordinates match the Three.js environment.


LOCATIONS = {

    # --------------------------------------------------
    # Woodland Clearing
    # --------------------------------------------------

    "woodland_clearing": {
        "id": "woodland_clearing",
        "name": "Woodland Clearing",
        "description": (
            "An open grassy area surrounded by woodland."
        ),
        "type": "natural_landmark",

        "x": 0,
        "z": 0,

        "radius_x": 3.5,
        "radius_z": 3.5,
    },

    # --------------------------------------------------
    # Woodland Pond
    # --------------------------------------------------

    "woodland_pond": {
        "id": "woodland_pond",
        "name": "Woodland Pond",
        "description": (
            "A small pond surrounded by stones "
            "and vegetation."
        ),
        "type": "natural_landmark",

        "x": 7,
        "z": 4,

        "radius_x": 4.1,
        "radius_z": 2.9,
    },

    # --------------------------------------------------
    # Fallen Log
    # --------------------------------------------------

    "fallen_log": {
        "id": "fallen_log",
        "name": "Fallen Log",
        "description": (
            "A fallen tree trunk resting among "
            "the woodland scenery."
        ),
        "type": "woodland_feature",

        "x": -10,
        "z": -13,

        "radius_x": 2.5,
        "radius_z": 1.6,
    },
}


# --------------------------------------------------
# Location lookup
# --------------------------------------------------

def get_location(location_id):
    """Return a location using its unique ID."""

    return LOCATIONS.get(location_id)


def get_location_at(x, z):
    """
    Check whether coordinates fall inside a known location.

    Returns the matching location, or None if Pebble
    isn't currently inside a recognised location.
    """

    for location in LOCATIONS.values():

        # Measure distance from the location's centre.
        distance_x = (
            (x - location["x"]) / location["radius_x"]
        )

        distance_z = (
            (z - location["z"]) / location["radius_z"]
        )

        # Use an ellipse to define the recognition area.
        distance = distance_x ** 2 + distance_z ** 2

        if distance <= 1:
            return location

    return None
