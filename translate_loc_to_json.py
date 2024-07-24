#!/usr/bin/env python

import csv
import json

import os
from typing import Any, Dict, List, NamedTuple, Tuple

map_image_side_length_px = 2048

class MapLocation(NamedTuple):
    map: str
    x: int
    y: int

def pos_x_to_map_y(pos_x: float) -> int:
    map_y = ((pos_x + 165))/480*map_image_side_length_px
    # return 512
    return round(map_y)

def pos_y_to_map_x(pos_y: float) -> int:
    map_x = (480-(pos_y + 165))/480*map_image_side_length_px
    # return 512
    return round(map_x)

class Section(NamedTuple):
    name: str
    location_id: int
    region: str
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
    access_rules: List[str]


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


def load_location_access_rules() -> Dict[str, List[str]]:
    with open("data/location_access_rules.json") as file:
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
        location_reader = csv.DictReader(file)
        potchestrace_positions: PotRaceChestPositionTable = (
            load_potracechest_positions()
        )
        npc_positions: NPCPositionTable = load_npc_positions()
        npc_lookup: Dict[str, str] = load_npc_lookup()
        location_access_rules: Dict[str, List[str]] = load_location_access_rules()
        for location in location_reader:
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
            try:
                access_rules = location_access_rules[location["shortname"]]
            except KeyError:
                access_rules = []
            locations[location["longname"]] = GatorLocationData(
                long_name=location["longname"],
                short_name=location["shortname"],
                location_id=id,
                client_id=client_id,
                client_name_id=client_name_id,
                region=location["ap_region"],
                location_group=location["ap_location_group"],
                pos=(pos_x, pos_y),
                access_rules=access_rules,
            )
    return locations


def construct_section(location: GatorLocationData) -> Section:
    return Section(
        name=location.long_name,
        location_id=location.location_id,
        region=location.region,
        client_id=location.client_id,
        client_name_id=location.client_name_id,
        location_group=location.location_group,
        access_rules=location.access_rules,
    )._asdict()


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
        section_names = [location.long_name for location in locations]
        common_prefix = os.path.commonprefix(section_names)
        if common_prefix != "":
            parts = common_prefix.partition(" - ")
            if location_pos == (5.362534, 154.2351):
                namey_name = "Junk 4 Trash"
            elif location_pos == (267.8625, 73.81152):
                namey_name = "Flint (BombBowl Mole)"
            elif location_pos == (-56.216, 220.591):
                namey_name = "Sam (Pencil Jackal)"
            elif location_pos == (-78.2, -106.54):
                namey_name = "Ninja Clan"
            else:
                namey_name = parts[2].removesuffix(" Quest Completion ").removesuffix(" Quest Completion NPC").removesuffix(" Quest Completion").removesuffix(" ")
        else:
            namey_name = str(location_pos)
        if namey_name == "":
            namey_name = str(location_pos)
        
        location_data_table[location_pos] = LocationData(
            name=namey_name,
            region=locations[0].region,
            access_rules=[],
            map_locations=[
                MapLocation(map="the_island", x=pos_x_to_map_y(location_pos[1]), y=pos_y_to_map_x(location_pos[0]))._asdict()
            ],
            sections=[construct_section(location) for location in locations],
        )._asdict()
    return location_data_table


def define_region(
    region_name: str,
    region_access_rules: Dict[str, List[str]],
    sectioned_location_table: LocationDataTable,
) -> RegionData:
    return RegionData(
        name=region_name,
        access_rules=region_access_rules[region_name],
        children=[
            location_data
            for (_, location_data) in sectioned_location_table.items()
            if location_data["region"] == region_name
        ]
        + [
            define_region(child_name, region_access_rules, sectioned_location_table)
            for child_name in gator_regions[region_name]
        ],
    )._asdict()

def traverse(dic, path=None):
    if not path:
        path=""
    if isinstance(dic,dict):
        try:
            name = dic["name"]
            local_path = path + "/" + name
            try:
                sections = dic["sections"]
                for section in sections:
                    for b in traverse(section, local_path):
                        yield b
            except:
                try:
                    children = dic["children"]
                    for child in children:
                        for b in traverse(child, local_path):
                            yield b
                except (KeyError):
                    yield local_path, dic
        except (KeyError):
            yield path, dic
    else: 
        yield path,dic
    #https://stackoverflow.com/questions/11929904/traverse-a-nested-dictionary-and-get-the-path-in-python

def convert_regions_to_lua(regions : RegionData) -> str:
    lua_data = "LOCATION_MAPPING = {\n"
    for x in traverse(regions):
        location_id = x[1]["location_id"]
        location_path = "@" + x[0].removeprefix("/")
        lua_data += "    [" + str(location_id) + "] = {\"" + location_path + "\"},\n"
    lua_data += "}"
    return lua_data

class NamedTupleEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, NamedTuple):
            return super().default(o._asdict())
        return super().default(o)

def export_json():
    starting_region = "Tutorial Island"
    region_access_rules = load_region_access_rules()
    regions = define_region(
        region_name=starting_region,
        region_access_rules=region_access_rules,
        sectioned_location_table=construct_sectioned_locations(load_location_csv()),
    )

    with open("locations_raw.json", "w") as file:
        json.dump([regions], file, indent=4, cls=NamedTupleEncoder)

def export_lua():
    starting_region = "Tutorial Island"
    region_access_rules = load_region_access_rules()
    regions = define_region(
        region_name=starting_region,
        region_access_rules=region_access_rules,
        sectioned_location_table=construct_sectioned_locations(load_location_csv()),
    )

    lua_data = convert_regions_to_lua(regions)

    with open("location_mapping.lua","w") as file:
        file.write(lua_data)


region_access_rules: Dict[str, List[str]] = load_region_access_rules()
gator_regions: Dict[str, List[str]] = {
    "Menu": ["Tutorial Island"],
    "Tutorial Island": [
        "Big Island",
        "Tutorial Island Races",
        "Tutorial Island Breakables",
        "Pots Shootable from Tutorial Island",
    ],
    "Pots Shootable from Tutorial Island": [],
    "Tutorial Island Races": [],
    "Tutorial Island Breakables": [],
    "Big Island": [
        "Big Island Races",
        "Big Island Breakables",
        "Mountain",
        "Junk 4 Trash",
        "Big Island Bracelet Shops",
    ],
    "Big Island Races": [],
    "Big Island Breakables": [],
    "Mountain": ["Mountain Breakables"],
    "Mountain Breakables": [],  # Intentionally omitting connection to Pots Shootable because avoiding loop, dealt with via access rules
    "Junk 4 Trash": [],
    "Big Island Bracelet Shops": [],
}

export_json()
export_lua()