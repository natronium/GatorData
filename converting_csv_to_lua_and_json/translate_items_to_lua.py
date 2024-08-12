import csv
import enum
import json
from typing import Any, Dict, List, NamedTuple, Set

class ItemGroup(enum.Enum):
    Friends = enum.auto()
    Crafting_Materials = enum.auto()
    Traversal = enum.auto()
    Hat = enum.auto()
    Quest_Item = enum.auto()
    Sword = enum.auto()
    Shield = enum.auto()
    Ranged = enum.auto()
    Craft = enum.auto()
    Item = enum.auto()
    Cardboard_Destroyer = enum.auto()

class GatorItemData(NamedTuple):
    long_name: str
    short_name: str
    item_id: int
    client_name_id: str
    client_resource_amount: int
    client_item_type: str
    classification: str
    base_quantity_in_item_pool: int
    item_groups: List[ItemGroup]

class GatorItemTable(Dict[str,GatorItemData]):
    def short_to_long(self, short_name: str) -> str:
        for _, data in self.items():
            if data.short_name == short_name:
                return data.long_name
        return None

class GatorItemPopData(NamedTuple):
    name: str
    type: str
    img: str
    codes: str

# Cardboard Destroyer Group
def is_destroyer(groups: List[ItemGroup])  -> bool:
    sword_destroyer : Set[ItemGroup] = {ItemGroup["Sword"], ItemGroup["Item"]}
    shield_destroyer : Set[ItemGroup] = {ItemGroup["Shield"], ItemGroup["Item"]}
    ranged_destroyer : Set[ItemGroup] = {ItemGroup["Ranged"], ItemGroup["Item"]}
    return set(groups).issuperset(sword_destroyer) or set(groups).issuperset(shield_destroyer) or set(groups).issuperset(ranged_destroyer)

def construct_client_item_type(client_item_type: str) -> str:
    if client_item_type == "Craft Stuff":
        return "Craft_Stuff"
    elif client_item_type == "Friends":
        return "Friend"
    else:
        return client_item_type


def load_item_csv() -> GatorItemTable:
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files  # type: ignore

    items : GatorItemTable = GatorItemTable()
    with open("data/item_lookup.csv") as file:
        item_reader = csv.DictReader(file)
        for item in item_reader:
            id = int(item["ap_item_id"]) if item["ap_item_id"] else None
            client_resource_amount = int(item["client_resource_amount"]) if item["client_resource_amount"] else None
            classification = item["ap_item_classification"]
            quantity = int(item["ap_base_quantity"]) if item["ap_base_quantity"] else 0
            groups = {ItemGroup[group] for group in item["ap_item_groups"].split(",") if group}
            client_item_type = construct_client_item_type(item["client_item_type"])
            if is_destroyer(groups):
                groups.add(ItemGroup["Cardboard_Destroyer"])
            items[item["longname"]] = GatorItemData(item["longname"], item["shortname"], id, item["client_name_id"],client_resource_amount,client_item_type, classification, quantity, groups)._asdict()
    return items

def get_item_code(item: GatorItemData) -> str:
    if item["short_name"] == "bowling_bomb":
        return "bomb"
    if item["short_name"] == "cheese_sandwich":
        return "sandwich"
    return item["short_name"]

def get_item_type(item: GatorItemData) -> str:
    if item["short_name"] == "bracelet" or item["short_name"] == "thrown_pencil":
        return "consumable"
    else:
        return "toggle"

def get_item_image(item: GatorItemData) -> str:
    base_path = "images/items/"
    ext =  ".png"
    return base_path + item["short_name"] + ext

def convert_items_to_lua(items: GatorItemTable) -> str:
    lua_data = "ITEM_MAPPING = {\n"
    for _, data in items.items():
        item_id = data["item_id"]
        item_code = get_item_code(data)
        if item_code != "bracelet" and item_code != "thrown_pencil":
            item_type = "toggle"
        else:
            item_type = "consumable"
        lua_data += "    [" + str(item_id) + "] = {\"" + item_code +"\", \"" + item_type + "\"},\n"

    lua_data += "}"
    return lua_data

def export_lua():

    lua_data = convert_items_to_lua(load_item_csv())

    with open("item_mapping.lua","w") as file:
        file.write(lua_data)

class SetItemGroupEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Set):
            string = ""
            for itemgroup in o:
                string += itemgroup.name
                string += ","
            return string.removesuffix(",")
        return super().default(o)

def export_json():

    items = load_item_csv()

    for name,item in items.items():
        item["short_name"] = get_item_code(item)
        items[name] = item

    with open("items.json","w") as file:
        json.dump([items], file, indent=4, cls=SetItemGroupEncoder)

def export_pop_json():
    items = load_item_csv()
    pop_items : List[GatorItemPopData] = []
    for _, item in items.items():
        pop_items.append(GatorItemPopData(name=item["long_name"],type=get_item_type(item),img=get_item_image(item), codes=get_item_code(item))._asdict())

    with open("items_pop.json","w") as file:
        json.dump(pop_items, file, indent=4, cls=SetItemGroupEncoder)


export_lua()
export_json()
export_pop_json()