#!/usr/bin/env python

import csv
import json

from typing import Dict, NamedTuple, Set, List, Tuple


class MapLocation(NamedTuple):
    map: str
    x: int
    y: int


class Section(NamedTuple):
    name: str
    location_id: int
    client_id: int
    client_name_id: str
    location_group: str
    access_rules: List[str]


class GatorLocationData(NamedTuple):
    long_name: str
    short_name: str
    location_id: int
    client_id: int
    client_name_id: str
    region: str
    location_group: str
    pos: Tuple[int, int]


class LocationData(NamedTuple):
    name: str
    region: str
    access_rules: List[str]
    map_locations: List[MapLocation]
    sections: List[Section]


class LocationDataTable(Dict[Tuple[int, int], LocationData]):
    def nothing():
        return


class GatorLocationTable(Dict[str, GatorLocationData]):
    def short_to_long(self, short_name: str) -> str:
        for _, data in self.items():
            if data.short_name == short_name:
                return data.long_name
        return None


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


class RegionData(NamedTuple):
    name: str
    access_rules: List[str]
    children: List[Dict]


def load_region_access_rules() -> Dict[str, List[str]]:
    with open("data/region_access_rules.json") as file:
        return json.load(file)


def load_potracechest_positions() -> PotRaceChestPositionTable:
    positions: PotRaceChestPositionTable = PotRaceChestPositionTable()
    with open("data/pot_chest_race_positions.json") as file:
        position_reader = json.load(file)
        for position in position_reader:
            id: int = int(position["id"]) if position["id"] else None
            pos_x: float = position["pos"][0]
            pos_y: float = position["pos"][1]
            positions[id] = PotRaceChestPositionData(id, pos_x, pos_y)
    return positions


def load_npc_lookup() -> Dict[str, str]:
    with open("data/npc_lookup.json") as file:
        return json.load(file)


def load_npc_positions() -> NPCPositionTable:
    positions: NPCPositionTable = NPCPositionTable()
    with open("data/npc_positions.json") as file:
        position_reader = json.load(file)
        for position in position_reader:
            name: str = position["name"]
            pos_x: float = position["pos"][0]
            pos_y: float = position["pos"][1]
            positions[name] = NPCPositionData(name, pos_x, pos_y)
    return positions


def load_location_csv() -> GatorLocationTable:
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files  # type: ignore

    locations: GatorLocationTable = GatorLocationTable()
    with open("data/location_lookup.csv") as file:
        item_reader = csv.DictReader(file)
        potchestrace_positions: PotRaceChestPositionTable = (
            load_potracechest_positions()
        )
        npc_positions: NPCPositionTable = load_npc_positions()
        npc_lookup: Dict[str, str] = load_npc_lookup()
        for location in item_reader:
            id: int | None = (
                int(location["ap_location_id"]) if location["ap_location_id"] else None
            )
            client_id: int | None = (
                int(location["client_id"]) if location["client_id"] else None
            )
            client_name_id: str = location["client_name_id"]
            if client_id != None:
                pos: PotRaceChestPositionData = potchestrace_positions[client_id]
                pos_x: float = pos.pos_x
                pos_y: float = pos.pos_y
            else:
                position_name: str = npc_lookup[client_name_id]
                try:
                    pos_x: float = npc_positions[position_name].pos_x
                    pos_y: float = npc_positions[position_name].pos_y
                except KeyError:
                    # Temporary until NPC positions for main/tutorial/multiple
                    pos_x: float = 0
                    pos_y: float = 0
            locations[location["longname"]] = GatorLocationData(
                long_name=location["longname"],
                short_name=location["shortname"],
                location_id=id,
                client_id=client_id,
                client_name_id=client_name_id,
                region=location["ap_region"],
                location_group=location["ap_location_group"],
                pos=(pos_x, pos_y),
            )
    return locations


def construct_section(location: GatorLocationData) -> Section:
    return Section(
        name=location.long_name,
        location_id=location.location_id,
        client_id=location.client_id,
        client_name_id=location.client_name_id,
        location_group=location.location_group,
        access_rules=[],
    )


def construct_sectioned_locations(
    gator_location_table: GatorLocationTable,
) -> LocationDataTable:
    location_data_table = LocationDataTable()
    positions = [gator_loc.pos for _, gator_loc in gator_location_table.items()]
    for location_pos in positions:
        locations = [
            gator_loc
            for _, gator_loc in gator_location_table.items()
            if gator_loc.pos == location_pos
        ]
        location_data_table[location_pos] = LocationData(
            name=str(location_pos),
            region=locations[0].region,
            access_rules=[],
            map_locations=[
                MapLocation(map="the_island", x=location_pos[0], y=location_pos[1])
            ],
            sections=[construct_section(location) for location in locations],
        )


def define_region(region_name, region_access_rules, location_table: LocationDataTable):
    return RegionData(
        name=region_name,
        access_rules=region_access_rules[region_name],
        children=[
            location_data
            for (_, location_data) in location_table.items()
            if location_data.region == region_name
        ]
        + [
            define_region(child_name, region_access_rules, location_table)
            for child_name in gator_regions[region_name]
        ],
    )


def export_json():
    locations: GatorLocationTable = load_location_csv()
    location_array = []
    for _, location in locations.items():
        location_array.append(location._asdict())

    with open("locations_raw.json", "w") as file:
        json.dump(location_array, file, indent=4)


region_access_rules: Dict[str, List[str]] = load_region_access_rules()
gator_regions: Dict[str, Set[str]] = {
    "Menu": {"Tutorial Island"},
    "Tutorial Island": {
        "Main Island",
        "Tutorial Island Races",
        "Tutorial Island Breakables",
    },
    "Tutorial Island Races": set(),
    "Tutorial Island Breakables": set(),
    "Main Island": {"Main Island Races", "Main Island Breakables", "Junk 4 Trash"},
    "Main Island Races": set(),
    "Main Island Breakables": {"Main Island Mountain Breakables"},
    "Main Island Mountain Breakables": set(),
    "Junk 4 Trash": set(),
}

# menu_region : RegionData = RegionData(name = "Menu", access_rules = )


export_json()
