import json
from typing import Dict
from PIL import Image, ImageFont, ImageDraw


def load_item_json() -> Dict[str,str]:
    items: Dict[str,str] = {}
    with open("items_pop.json") as file:
        item_reader = json.load(file)
        for item in item_reader:
            items[item["name"]] = item["img"]
    return items


# from https://stackoverflow.com/questions/68648801/generate-image-from-given-text
def text_to_image(
    text: str,
    font_filepath: str,
    font_size: int,
    color: str,
    # fill_color: str,
):
    font = ImageFont.truetype(font_filepath, size=font_size)
    canvas_size = (200,100)
    img = Image.new("RGBA", canvas_size)

    draw = ImageDraw.Draw(img)
    draw_point = (0, 0)

    # bbox = draw.textbbox(draw_point, text, font)
    # draw.rectangle(bbox, fill=fill_color)
    draw.multiline_text(draw_point, text, font=font, fill=color)

    text_window = img.getbbox()
    img = img.crop(text_window)
    return img


for name, path in load_item_json().items():
    font_filepath = "C:\\Windows\\Fonts\\arialbd.ttf"
    multiline = name.split("(")[0].replace(" ","\n")
    new_multiline_array = multiline.split("\n")
    for i, line in enumerate(multiline.split("\n")):
        if len(line) > 8:
            new_line = line[0:5] + "-\n" + line[5:]
            new_multiline_array[i] = new_line
    new_multiline = "\n".join(str(x) for x in new_multiline_array)
    img = text_to_image(new_multiline, font_filepath, 14, "white")
    img.save(path)
