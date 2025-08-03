import math
import os
import csv
import nbtlib
from nbtlib import File
from PIL import Image

import json


def load_block_colors(path):
    parsed_data = {}

    with open(path, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Access by column names
            name = row.get("name", "")
            color_hex = row.get("colour", "").strip()

            if not name or not color_hex:
                print(f"malformed row: {row}")
                continue

            if len(color_hex) == 8:  # Expecting ARGB format
                try:
                    a = int(color_hex[0:2], 16)
                    r = int(color_hex[2:4], 16)
                    g = int(color_hex[4:6], 16)
                    b = int(color_hex[6:8], 16)
                    parsed_data[name] = (r, g, b)
                except ValueError:
                    print(f"Invalid color hex: {color_hex} in row: {row}")
            else:
                print(f"Malformed ARGB length: {color_hex} in row: {row}")

    return parsed_data


# Usage
BLOCK_COLORS = load_block_colors("mc-materials.csv")
def darken_color(color: tuple[int, int, int], percent: float) -> tuple[int, int, int]:
    """Darken an RGBA color by a percentage (0.0 to 1.0)."""
    r, g, b = color
    factor = 1.0 - percent
    return (
        max(0, int(r * factor)),
        max(0, int(g * factor)),
        max(0, int(b * factor))
    )





def render_pixel(x, y, z, width, length, height, block_data, id_to_block, img, pixelcoord_x, pixelcoord_y,
                 depth) -> bool:
    idx = y * length * width + z * width + x
    block_id = block_data[idx]
    block_name = id_to_block[block_id] if block_id < len(id_to_block) else "minecraft:air"

    if block_name != "minecraft:air" and block_name != "cave_air":
        if block_name not in BLOCK_COLORS:
            print(f"block color unknown for: " + block_name)
        color: tuple[int,int,int] = BLOCK_COLORS.get(block_name, (255, 0, 255))  # magenta fallback
        #print(f"color block {block_name} -> {color}")
        factor = 0.5
        shift = 1
        if (max(color)+shift)*factor > 1: # very bright blocks (like ice)
            shift = 0
            factor = .25
        color = darken_color(color, (math.sqrt(depth)-shift)*factor)
        # Note: image coordinates are (z, height - 1 - y)
        img.putpixel((pixelcoord_x, pixelcoord_y), color)
        return True
    return False


def render_schematic_side(filepath: str) -> Image.Image:
    root = File.load(filepath, gzipped=True)  # loads Compound

    width = root["Width"]
    height = root["Height"]
    length = root["Length"]

    palette = root["Palette"]
    block_data = root["BlockData"]  # ByteArray

    # Invert palette: id -> block_name (without block states)
    id_to_block = [None] * (max(palette.values()) + 1)
    for block_name, idx in palette.items():
        id_to_block[idx] = block_name.split("[")[0]  # remove block states

    # Create an empty image for side view (Z horizontal, Y vertical)
    img = Image.new("RGBA", (length + width + width + 2, max(width, length, height)), (0, 0, 0, 0))

    # FRONT
    for y in range(height):  # EACH ROW BOTTOM TO TOP
        for z in range(length):  # EACH COLUMN LEFT TO RIGHT
            for x in range(width):  # take first from this dimension
                if render_pixel(x, y, z, width, length, height, block_data, id_to_block, img, z, height - 1 - y, x / width):
                    break
    # SIDE
    for y in range(height):
        for x in range(width):
            for z in range(length):
                if render_pixel(x, y, z, width, length, height, block_data, id_to_block, img, x + length + 1,
                                height - 1 - y, z / length):
                    break

    # TOP

    for x in range(width):  # EACH ROW
        for z in range(length):  # EACH COLUMN IN ROW
            for y in range(height - 1, 0, -1):  # EACH ROW BOTTOM TO TOP
                if render_pixel(x, y, z, width, length, height, block_data, id_to_block, img, x + length + width + 2, z,
                               (height - y) / height):
                    break
    return img


def find_schem_files(root_path):
    schem_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.lower().endswith('.schem'):
                full_path = os.path.join(dirpath, filename)
                schem_files.append(full_path)
    return schem_files


def resize_to_height(img: Image.Image, target_height: int = 100) -> Image.Image:
    width, height = img.size
    aspect_ratio = width / height
    new_width = int(target_height * aspect_ratio)
    return img.resize((new_width, target_height), Image.Resampling.NEAREST)


def main():
    rootDir = "C:/Users/Max1M/Downloads"
    output_path = "./dannypan/"

    files = find_schem_files(rootDir)
    for path in files:
        img = render_schematic_side(path)
        img = resize_to_height(img, 200)
        filename = os.path.basename(path).replace(".schem", ".png")
        filePath = output_path + "/" + filename
        img.save(filePath)
        print(f"Saved rendered image to {filePath}")


if __name__ == "__main__":
    main()
