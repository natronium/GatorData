#!/usr/bin/env python

import csv
import enum
import os

from typing import Dict, NamedTuple

class LocationGroup(enum.Enum):
    Pot = enum.auto()
    Chest = enum.auto()
    Race = enum.auto()

class GatorLocationData(NamedTuple):
    long_name: str
    short_name: str
    location_id: int
    client_id: int
    client_name_id: str
    region: str
    location_group: LocationGroup

class GatorLocationTable(Dict[str,GatorLocationData]):
    def short_to_long(self, short_name: str) -> str:
        for _, data in self.items():
            if data.short_name == short_name:
                return data.long_name
        return None

# Locations: quest completions, ground pickups, races, bracelet purchases, junk 4 trash
def load_location_csv():
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files  # type: ignore

    locations : GatorLocationTable = GatorLocationTable()
    with open("data/location_lookup.csv") as file:
        item_reader = csv.DictReader(file)
        for location in item_reader:
            id = int(location["ap_location_id"]) if location["ap_location_id"] else None
            client_id = int(location["client_id"]) if location["client_id"] else None
            group = LocationGroup[location["ap_location_group"]] if location["ap_location_group"] else None
            locations[location["longname"]] = GatorLocationData(location["longname"], location["shortname"], id, client_id, location["client_name_id"], location["ap_region"], group)
    return locations

locations : GatorLocationTable = load_location_csv()
print(locations)