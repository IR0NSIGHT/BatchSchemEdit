import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

import nbtlib

from BlockMappingTable import block_mapping_table

BLOCK_LIST_FILE = "./minecraft_blocks.txt"


class ToolTip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def load_schem_files(schem_files):
    schem_data_dict = {}

    for schem_file in schem_files:
        schem_data = nbtlib.File.load(schem_file, gzipped=True)
        schem_data_dict[schem_file] = schem_data

    return schem_data_dict


def replace_blocks(schem_data, block_to_replace, replace_with):
    replaced_blocks = 0
    if not schem_data:
        return "Invalid schematic data"

    if 'Palette' in schem_data:
        palette = schem_data['Palette']

        if "[" not in block_to_replace and "[" in replace_with and any(
                replace_with.split("[")[0] + "[" in item for item in palette):
            return "Please remove the properties of the replacement block (everything in brackets) to prevent conflicts."

        if block_to_replace == replace_with:
            return "The 'block_to_replace' and 'replace_with' are identical. No need to replace blocks."

        found = False

        for block in palette:
            if "[" not in block_to_replace:
                if block_to_replace == block.split("[")[0]:
                    found = True
                    break
            else:
                if block_to_replace in block:
                    found = True
                    break

        if found == False:
            return f"No matching blocks found for: {block_to_replace}"

        if "[" not in block_to_replace:
            changes = []

            for block in palette:
                if block_to_replace == block.split("[")[0]:
                    new_key = block.replace(block_to_replace, replace_with)
                    changes.append((block, new_key))

            for old_key, new_key in changes:
                palette[new_key] = palette.pop(old_key)
        else:
            if replace_with in palette:
                to_replace_index = palette[block_to_replace]
                replace_with_index = palette[replace_with]
                block_data = schem_data['BlockData']

                block_data_bytes = bytearray(block_data)

                modified = False
                for i, block in enumerate(block_data_bytes):
                    if block == to_replace_index:
                        block_data_bytes[i] = replace_with_index
                        modified = True

                if modified:
                    schem_data['BlockData'] = nbtlib.ByteArray(block_data_bytes)

                del palette[block_to_replace]
            else:
                palette[replace_with] = palette.pop(block_to_replace)

        replaced_blocks += 1

        schem_data['PaletteMax'] = nbtlib.Int(len(palette))

        return f"Replaced {replaced_blocks} blocks"


def save_schem_file(schem_data, filepath):
    try:
        schem_data.save(filepath)
    except Exception as e:
        return f"Error saving file: {e}"


def get_unique_blocks_from_modified_data(modified_schem_data):
    unique_blocks: set[str] = set()

    for schem_data in modified_schem_data.values():
        palette = schem_data.get('Palette', {})

        for block in palette:
            unique_blocks.add(block)
    blocks_no_params = []
    for block in unique_blocks:
        cleaned = re.sub(r"\[.*?\]", "", block)
        blocks_no_params.append(cleaned)
    for block in blocks_no_params:
        unique_blocks.add(block)
    return unique_blocks


unsaved_changes = False


def update_mappings(mappings: dict[str, str]) -> None:
    print("hello world")


def load_block_list(filepath: str = BLOCK_LIST_FILE) -> list[str]:
    with open(filepath, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def write_block_list(blocks: list[str], filepath: str = BLOCK_LIST_FILE) -> None:
    with open(filepath, "w", encoding="utf-8") as file:
        for block in blocks:
            file.write(block + "\n")


def get_current_mappings() -> dict[str, str]:
    return {}


# GUI
def main():
    def show_message(title, message, buttons=False):
        def close_dialog(result=None):
            top.result = result
            top.destroy()

        if message == "":
            print("nothing to do.")
            return
        top = tk.Toplevel()
        top.title(title)

        text = tk.Text(top, wrap=tk.NONE, state=tk.DISABLED)
        text.configure(state=tk.NORMAL)
        text.insert(tk.END, message)
        text.configure(state=tk.DISABLED)

        lines = int(text.index(tk.END).split('.')[0])
        text.configure(height=min(lines, 25))

        max_line_length = max(len(line) for line in message.splitlines()) + 5
        text.configure(width=min(max_line_length, 125))

        scroll = tk.Scrollbar(top, command=text.yview)
        text.configure(yscrollcommand=scroll.set)

        text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        top.grid_rowconfigure(0, weight=1)
        top.grid_columnconfigure(0, weight=1)

        button_frame = tk.Frame(top)
        button_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='e')

        if buttons:
            yes_button = tk.Button(button_frame, text="Yes", command=lambda: close_dialog(True), width=10)
            yes_button.pack(side=tk.LEFT, padx=(0, 10))

            no_button = tk.Button(button_frame, text="No", command=lambda: close_dialog(False), width=10)
            no_button.pack(side=tk.LEFT)
        else:
            ok_button = tk.Button(button_frame, text="OK", command=lambda: close_dialog(True), width=10)
            ok_button.pack()

        top.wait_window()
        return top.result

    def set_input_widgets_state(state):
        button_save_changes.config(state=state)
        button_save_copy.config(state=state)

    def on_replace_blocks(mappings: dict[str, str]):
        global unsaved_changes
        nonlocal modified_schem_data
        valid_mappings = {}
        for block, replacement in mappings.items():
            if replacement == "":  # ignore mappings that are not set
                continue
            if replacement == block:
                continue
            if "minecraft" not in block or "minecraft" not in replacement:
                messagebox.showerror("Replace Blocks", "Blocks should be preceded with \"minecraft:\".")
                return
            elif block == "" or replacement == "":
                messagebox.showerror("Replace Blocks", "Please fill out all fields.")
                return
            valid_mappings[block] = replacement

        messages = []
        for filepath in new_schem_files:
            schem_data = modified_schem_data.get(filepath)
            for block, replacement in valid_mappings.items():
                message = replace_blocks(schem_data, block, replacement)
                messages.append(f"{os.path.basename(filepath)}: {message}")
            modified_schem_data[filepath] = schem_data

        unsaved_changes = True
        root.title(".Schem Block Replacer (Unsaved Changes)")
        update_master_list(modified_schem_data)
        show_message("Blocks Replaced", "\n".join(messages), False)

        update_known_block_list(list(get_current_mappings().keys()))

    def update_known_block_list(blocks: list[str]):
        print(f"adding blocks: {blocks}")
        block_suggestions = set(load_block_list(BLOCK_LIST_FILE))
        for block in blocks:
            block_suggestions.add(block)
        write_block_list(sorted(list(block_suggestions)), BLOCK_LIST_FILE)

    def on_open_files():
        global unsaved_changes
        nonlocal modified_schem_data, new_schem_files
        if unsaved_changes:
            if not messagebox.askyesno("Exit",
                                       "There are unsaved changes. Are you sure you want to load new .schem file(s)?"):
                return

        new_schem_files = filedialog.askopenfilenames(title="Select .schem file(s)",
                                                      filetypes=[("Schem Files", "*.schem")])
        if new_schem_files:
            modified_schem_data = load_schem_files(new_schem_files)
            update_master_list(modified_schem_data)
            set_input_widgets_state(tk.NORMAL)
            unsaved_changes = False
            root.title(".Schem Block Replacer")

    def update_master_list(modified_schem_data):
        unique_blocks = list(get_unique_blocks_from_modified_data(modified_schem_data))
        unique_blocks = sorted(unique_blocks, key=lambda x: x.split(':', 1)[1])

        # Add block types to mappings list, keep existing mappings if already exists
        old_mappings: dict[str, str] = get_current_mappings()
        new_mappings = {}
        for block in unique_blocks:
            new_mappings[block] = old_mappings.get(block, "")
        update_mappings(new_mappings)

        num_files = len(modified_schem_data)
        if num_files == 1:
            master_list_label_text.set("Full List of All Unique Blocks in 1 File")
        else:
            master_list_label_text.set(f"Full List of All Unique Blocks in {num_files} files")

    def on_save_changes():
        global unsaved_changes
        saved_filepaths = []

        filepaths_str = "\n".join(modified_schem_data.keys())
        confirm_message = f"The following .schem files will be overwritten:\n\n{filepaths_str}\n\nDo you want to continue?"
        confirm = show_message("Overwrite Confirmation", confirm_message, True)

        if not confirm:
            return

        for filepath, schem_data in modified_schem_data.items():
            save_schem_file(schem_data, filepath)
            saved_filepaths.append(filepath)

        unsaved_changes = False
        root.title(".Schem Block Replacer")

        saved_filepaths_str = "\n".join(saved_filepaths)
        show_message("Changes Saved", f"Changes saved to the original .schem files:\n{saved_filepaths_str}", False)

    def on_save_copy():
        global unsaved_changes
        saved_filepaths = []

        new_filepaths = [filepath.split(".")[0] + "_copy.schem" for filepath in modified_schem_data.keys()]
        filepaths_str = "\n".join(new_filepaths)
        confirm_message = f"The following .schem files will be created or overwritten:\n\n{filepaths_str}\n\nDo you want to continue?"
        confirm = show_message("Save to Copies Confirmation", confirm_message, True)

        if not confirm:
            return

        for filepath, schem_data in modified_schem_data.items():
            new_filepath = filepath.split(".")[0] + "_copy.schem"
            save_schem_file(schem_data, new_filepath)
            saved_filepaths.append(new_filepath)

        unsaved_changes = False
        root.title(".Schem Block Replacer")

        saved_filepaths_str = "\n".join(saved_filepaths)
        show_message("Changes Saved", f"Changes saved to the original .schem files:\n{saved_filepaths_str}", False)

    def on_save_settings():
        print("save settings")
        mappings = get_current_mappings()
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        file_path = filedialog.asksaveasfilename(
            title="Save Mappings As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not file_path:
            return  # User canceled

        with open(file_path, "w", encoding="utf-8") as f:
            for key, value in mappings.items():
                if value == "":
                    continue
                f.write(f"{key}\t{value}\n")

    def on_load_settings():
        print("load settings")
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        file_path = filedialog.askopenfilename(
            title="Open Mapping File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not file_path:
            return {}

        mappings_from_file = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "\t" not in line:
                    continue  # skip empty or malformed lines
                key, value = line.split("\t", 1)
                mappings_from_file[key] = value
        old_mappings = get_current_mappings()
        for block, replacement in mappings_from_file.items():
            old_mappings[block] = mappings_from_file[block]
        update_mappings(old_mappings)

    def on_reset_settings():
        """reset to only show blocks in the current schematics state"""
        unique_blocks = list(get_unique_blocks_from_modified_data(modified_schem_data))
        unique_blocks = sorted(unique_blocks, key=lambda x: x.split(':', 1)[1])

        # Add block types to mappings list, keep existing mappings if already exists
        new_mappings = {}
        for block in unique_blocks:
            new_mappings[block] = ""
        update_mappings(new_mappings)

    def on_reset_state():
        """
        resets the state of the table, wiping all entries and unloading all schematics.
        :return:
        """
        update_mappings({})

        global unsaved_changes
        nonlocal new_schem_files, modified_schem_data
        new_schem_files = []
        modified_schem_data = {}
        master_list_label_text.set("No schem files loaded.")
        set_input_widgets_state(tk.DISABLED)
        unsaved_changes = False

    def on_exit():
        global unsaved_changes
        if unsaved_changes:
            if messagebox.askyesno("Exit", "There are unsaved changes. Are you sure you want to exit?"):
                root.destroy()
        else:
            root.destroy()

    def remove_properties(entry, update_func):
        new_text = update_func()
        entry.delete(0, tk.END)
        entry.insert(0, new_text)

    def show_credits():
        messagebox.showinfo("Program Credits",
                            "Author:\nEthan Hackett\n(Discord: northernmockingbird)\nEdited: Ir0nsight\nGithub: https://github.com/IR0NSIGHT")

    root = tk.Tk()
    root.title(".schem Block Replacer v2.0")
    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.geometry("1000x500")

    new_schem_files = []
    modified_schem_data = {}

    master_list_label_text = tk.StringVar()
    master_list_label = tk.Label(root, textvariable=master_list_label_text, anchor=tk.W)
    master_list_label.pack(fill=tk.X, padx=10)

    frame_master_list = tk.Frame(root)
    frame_master_list.pack(side=tk.LEFT, padx=10, pady=0, fill=tk.BOTH, expand=True)

    block_suggestions = sorted(list(set(load_block_list(BLOCK_LIST_FILE))))
    [update_mappings, get_current_mappings] = block_mapping_table(frame_master_list, {}, block_suggestions,
                                                                  on_replace_blocks)

    frame_input = tk.Frame(root)
    frame_input.pack(side=tk.RIGHT, padx=10, pady=10)

    button_open_files = tk.Button(frame_input, text="Open .schem(s)", command=on_open_files)
    button_open_files.pack(pady=10)
    ToolTip(button_open_files, "Load .schem(s) into BatchSchemEdit app")

    button_save_changes = tk.Button(frame_input, text="Save .schem(s)", command=on_save_changes)
    button_save_changes.pack(pady=5)
    ToolTip(button_save_changes, "Save .schem(s) and overwrite the original files")

    button_save_copy = tk.Button(frame_input, text="Save to _copy.schem", command=on_save_copy)
    button_save_copy.pack(pady=5)
    ToolTip(button_save_copy, "Save .schem(s) with the suffix '_copy' to file without editing the originals")

    button_reset_all = tk.Button(frame_input, text="Unload .schem(s)", command=on_reset_state)
    button_reset_all.pack(pady=5)
    ToolTip(button_reset_all, "Unload .schem(s) and reset the table to a clean state")

    divider = tk.Frame(frame_input, height=2, bd=1, relief=tk.SUNKEN)
    divider.pack(fill=tk.X, padx=5, pady=10)

    button_save_mappings = tk.Button(frame_input, text="Save settings", command=on_save_settings)
    button_save_mappings.pack(pady=5)
    ToolTip(button_save_mappings, "Save all blocks+replacement that are not empty to a settings.txt to reuse it later")

    button_load_mappings = tk.Button(frame_input, text="Load settings", command=on_load_settings)
    button_load_mappings.pack(pady=5)
    ToolTip(button_load_mappings, "Load a settings.txt file that contains mappings")

    button_clear_table = tk.Button(frame_input, text="Clear settings", command=on_reset_settings)
    button_clear_table.pack(pady=5)
    ToolTip(button_clear_table, "Clear the settings, leave only blocks that exist in the loaded schematics")

    info_button = tk.Button(root, text="©", command=show_credits)
    info_button.place(in_=root, relx=1.0, rely=1.0, x=-2, y=-2, anchor="se")
    ToolTip(info_button, "Information")
    set_input_widgets_state(tk.DISABLED)

    root.mainloop()


if __name__ == "__main__":
    main()
