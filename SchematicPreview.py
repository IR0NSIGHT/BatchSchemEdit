import csv
import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
from nbtlib import File


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
        color: tuple[int, int, int] = BLOCK_COLORS.get(block_name, (255, 0, 255))  # magenta fallback
        factor = 0.5
        shift = 1
        if (max(color) + shift) * factor > 1:  # very bright blocks (like ice)
            shift = 0
            factor = .25
        color = darken_color(color, (math.sqrt(depth) - shift) * factor)
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
                if render_pixel(x, y, z, width, length, height, block_data, id_to_block, img, z, height - 1 - y,
                                x / width):
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


class RedirectText:
    """Redirect print to a Tkinter Text widget for live logging."""

    def __init__(self, text_ctrl):
        self.output = text_ctrl

    def write(self, string):
        self.output.configure(state='normal')
        self.output.insert(tk.END, string)
        self.output.see(tk.END)  # scroll to end
        self.output.configure(state='disabled')
        self.output.update_idletasks()  # force GUI update

    def flush(self):
        pass  # no-op for compatibility


def process_schematics(rootDir):
    last_dir = os.path.basename(os.path.normpath(rootDir))
    output_path = last_dir
    os.makedirs(output_path, exist_ok=True)

    files = find_schem_files(rootDir)
    print(f"Found {len(files)} schematic files in {rootDir}\n", flush=True)
    for path in files:
        try:
            print(f"Processing {path}...", flush=True)
            img = render_schematic_side(path)
            img = resize_to_height(img, 200)
            filename = os.path.basename(path).replace(".schem", ".png")
            filePath = os.path.join(output_path, filename)
            img.save(filePath)
            print(f"Saved image to {filePath}\n", flush=True)
        except Exception as e:
            print(f"An error occurred while processing {path}: {e}\n", flush=True)


def on_select_folder(text_widget):
    rootDir = filedialog.askdirectory(title="Select Root Directory")
    if not rootDir:
        messagebox.showwarning("No folder selected", "Please select a folder.")
        return

    # Clear previous messages
    text_widget.configure(state='normal')
    text_widget.delete('1.0', tk.END)
    text_widget.configure(state='disabled')

    # Redirect stdout to the text widget
    old_stdout = sys.stdout
    sys.stdout = RedirectText(text_widget)

    try:
        process_schematics(rootDir)
        messagebox.showinfo("Done", f"Processed schematics from:\n{rootDir}")
    finally:
        sys.stdout = old_stdout  # Restore stdout


def main():
    window = tk.Tk()
    window.title("Schematic Renderer")

    select_btn = tk.Button(window, text="Select Root Directory", command=lambda: on_select_folder(log_text))
    select_btn.pack(padx=20, pady=(20, 5))

    log_text = scrolledtext.ScrolledText(window, state='disabled', width=80, height=20)
    log_text.pack(padx=20, pady=(5, 20))

    window.mainloop()

if __name__ == "__main__":
    main()