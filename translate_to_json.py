#!/usr/bin/env python

import csv
import enum
import json

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
    pos_x: int
    pos_y: int

class PotRaceChestPositionData(NamedTuple):
    id: int
    pos_x: int
    pos_y: int

class PotRaceChestPositionTable(Dict[int, PotRaceChestPositionData]):
    # Stuff here
    def nothing():
        return

class NPCLookupData(NamedTuple):
    client_name_id: str
    position_name: str

class NPCLookupTable(Dict[str, NPCLookupData]):
    # Stuff here
    def nothing():
        return

class NPCPositionData(NamedTuple):
    name: str
    pos_x: int
    pos_y: int

class NPCPositionTable(Dict[str, NPCPositionData]):
    # Stuff here
    def nothing():
        return

class GatorLocationTable(Dict[str,GatorLocationData]):
    def short_to_long(self, short_name: str) -> str:
        for _, data in self.items():
            if data.short_name == short_name:
                return data.long_name
        return None

def load_potracechest_positions() -> PotRaceChestPositionTable:
    positions : PotRaceChestPositionTable = PotRaceChestPositionTable()
    with open("data/pot_chest_race_positions.json") as file:
        position_reader = json.load(file)
        for position in position_reader:
            id = int(position["id"]) if position["id"] else None
            pos_x = position["pos"][0]
            pos_y = position["pos"][1]
            positions[id] = PotRaceChestPositionData(id,pos_x,pos_y)
    return positions

def load_npc_lookup() -> NPCLookupTable:
    lookups : NPCLookupTable = NPCLookupTable()
    with open("data/npc_lookup.json") as file:
        lookup_reader = json.load(file)
        for lookup in lookup_reader:
            client_name_id = lookup["client_name_id"]
            position_name = lookup["position_name"]
            lookups[client_name_id] = NPCLookupData(client_name_id,position_name)
    return lookups

def load_npc_positions() -> NPCPositionTable:
    positions : NPCPositionTable = NPCPositionTable()
    with open("data/npc_positions.json") as file:
        position_reader = json.load(file)
        for position in position_reader:
            name = position["name"]
            pos_x = position["pos"][0]
            pos_y = position["pos"][1]
            positions[name] = NPCPositionData(name,pos_x,pos_y)
    return positions

def load_location_csv() -> GatorLocationTable:
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files  # type: ignore

    locations : GatorLocationTable = GatorLocationTable()
    with open("data/location_lookup.csv") as file:
        item_reader = csv.DictReader(file)
        potchestrace_positions : PotRaceChestPositionTable = load_potracechest_positions()
        npc_positions : NPCPositionTable = load_npc_positions()
        npc_lookup : NPCLookupTable = load_npc_lookup()
        for location in item_reader:
            id = int(location["ap_location_id"]) if location["ap_location_id"] else None
            client_id = int(location["client_id"]) if location["client_id"] else None
            client_name_id = location["client_name_id"]
            if client_id != None:
                pos : PotRaceChestPositionData = potchestrace_positions[client_id]
                pos_x : int = pos.pos_x
                pos_y : int = pos.pos_y
            else:
                position_name = npc_lookup[client_name_id].position_name
                try:
                    pos_x = npc_positions[position_name].pos_x
                    pos_y = npc_positions[position_name].pos_y
                except (KeyError):
                    # Temporary until NPC positions for main/tutorial/multiple
                    pos_x = 0
                    pos_y = 0
            locations[location["longname"]] = GatorLocationData(location["longname"], location["shortname"], id, client_id, client_name_id, location["ap_region"], location["ap_location_group"], pos_x, pos_y)
    return locations

locations : GatorLocationTable = load_location_csv()
file_string : str = "["
for _, location in locations.items():
    location_string : str = json.dumps(location._asdict())
    file_string += location_string
    file_string += ",\n"
file_string = file_string[:-2]
file_string += "]"
with open("locations_raw.json","w") as file:
    file.write(file_string)