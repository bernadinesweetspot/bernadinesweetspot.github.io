
# --------------------------------------------------
# Pebble's Environment: Known Locations
# --------------------------------------------------

# This file defines places that Pebble can recognise
# within its environment.

# Each location has:
# - A unique ID
# - A display name
# - A description
# - A centre position (x, z)
# - An area that determines when Pebble is there


LOCATIONS = {
    "woodland_pond": {
        "id": "woodland_pond",
        "name": "Woodland Pond",
        "description": (
            "A small pond surrounded by stones "
            "and vegetation."
        ),
        "type": "natural_landmark",

        # Centre of the pond in Three.js coordinates.
        "x": 7,
        "z": 4,

        # Approximate recognition area.
        # This includes the water and its surrounding bank.
        "radius_x": 4.1,
        "radius_z": 2.9,
    }
}


# --------------------------------------------------
# Look up locations
# --------------------------------------------------

def get_location(location_id):
    """
    Return a location using its unique ID.

    Returns None if the location doesn't exist.
    """

    return LOCATIONS.get(location_id)


def get_location_at(x, z):
    """
    Check whether coordinates fall inside a known location.

    Returns the matching location, or None if Pebble
    isn't currently inside a recognised location.
    """

    for location in LOCATIONS.values():

        # Work out how far the coordinates are from
        # the centre of this location.
        distance_x = (
            (x - location["x"]) / location["radius_x"]
        )

        distance_z = (
            (z - location["z"]) / location["radius_z"]
        )

        # An elliptical area allows the pond to have
        # different widths along its X and Z axes.
        distance = distance_x ** 2 + distance_z ** 2

        if distance <= 1:
            return location

    return None
