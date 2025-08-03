from nbtlib import File
from PIL import Image

import json


def load_block_colors(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    block_colors = {}
    for block in data.get("data", []):
        name = block.get("name")
        hex_color = block.get("color", "#000000")
        alpha = block.get("alpha", 255)

        # Convert hex color "#RRGGBB" to (R, G, B)
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        a = int(alpha * 255) if isinstance(alpha, float) else alpha
        block_colors[name] = (r, g, b, a)

    return block_colors


# Usage
BLOCK_COLORS = load_block_colors("vanilla_blocks.json")

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
    img = Image.new("RGBA", (length, height), (0, 0, 0, 0))

    # Iterate columns in X, Z, Y order, scan blocks from bottom to top
    # For each (z,y) column, find highest non-air block in X direction
    for y in range(height): # EACH ROW BOTTOM TO TOP
        for z in range(length): # EACH COLUMN LEFT TO RIGHT
            print(f"pixelpos {y},{z}")
            for x in range(width):
                idx = y * length * width + z * width + x
                block_id = block_data[idx]
                block_name = id_to_block[block_id] if block_id < len(id_to_block) else "minecraft:air"

                if block_name != "minecraft:air" and block_name != "cave_air":
                    color = BLOCK_COLORS.get(block_name, (255, 0, 255, 255))  # magenta fallback
                    print(f"{block_name} at {x},{y},{z}")
                    # Note: image coordinates are (z, height - 1 - y)
                    img.putpixel((z, height - 1 - y), color)
                    break  # Draw first visible block on this column

    return img

def main():
    schematic_path = "house_1.schem"
    output_path = "rendered_side.png"

    img = render_schematic_side(schematic_path)
    img.save(output_path)
    print(f"Saved rendered image to {output_path}")

if __name__ == "__main__":
    main()
