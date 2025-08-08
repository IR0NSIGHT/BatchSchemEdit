import tkinter as tk
from tkinter import ttk
from typing import Callable


class AutocompleteEntry(tk.Entry):
    def __init__(self, master, suggestions: list[str], **kwargs):
        super().__init__(master, **kwargs)
        self.suggestions = suggestions
        self.listbox = None
        self.bind("<KeyRelease>", self.on_key_release)

    def on_key_release(self, event):
        userString = self.get()
        if not userString:
            self.hide_suggestions()
            return

        filtered = [blockName for blockName in self.suggestions if userString in blockName]
        if filtered:
            if not self.listbox:
                self.show_suggestions()
            self.update_listbox(filtered)
        else:
            self.hide_suggestions()

    def show_suggestions(self):
        self.listbox = tk.Listbox(self.master, height=10)

        # Ensure dimensions are updated
        self.update_idletasks()

        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        width = self.winfo_width()

        self.listbox.place(x=x, y=y, width=width)
        self.listbox.bind("<<ListboxSelect>>", self.select_suggestion)

    def update_listbox(self, suggestions):
        self.listbox.delete(0, tk.END)
        for item in suggestions:
            self.listbox.insert(tk.END, item)

    def select_suggestion(self, event):
        if self.listbox.curselection():
            value = self.listbox.get(self.listbox.curselection()[0])
            self.delete(0, tk.END)
            self.insert(0, value)
        self.hide_suggestions()
        self.focus()

    def hide_suggestions(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None


def block_mapping_table(parent: tk.Widget, block_entries: dict[str, str], suggestion_blocks: list[str],
                        on_edit_callback=None) -> list[Callable[[dict[str, str]], None] | Callable[[], dict[str, str]]]:
    """
    table component with two columns: original, replacement.
    :param parent: Tk widget (frame/window) to insert the table into
    :param block_entries: dict of original -> replacement blocks
    :param suggestion_blocks: list of strings for autocomplete suggestions
    :param on_edit_callback: function to call with current mapping on button press
    :return: the frame containing the table and controls
    """

    frame = tk.Frame(parent)
    tree = ttk.Treeview(frame, columns=("original", "replacement"), show="headings")

    def get_current_mappings() -> dict[str, str]:
        mapping = {}
        for row in tree.get_children():
            values = tree.item(row, "values")
            key = values[0]
            value = values[1]
            mapping[key] = value
        return mapping

    def on_double_click(event):
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)

        if column != '#2' or not row_id:
            return

        x, y, _, height = tree.bbox(row_id, column=column)
        width = tree.column("replacement", option="width")
        print(f"colum width = {width}")
        replacement_value = tree.set(row_id, "replacement")

        entry = AutocompleteEntry(tree, suggestion_blocks)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, replacement_value)
        entry.focus()

        def save_edit(_):
            tree.set(row_id, "replacement", entry.get())
            entry.hide_suggestions()
            entry.destroy()

        entry.bind("<FocusOut>", save_edit)

    def on_run_callback():
        mapping = get_current_mappings()
        if on_edit_callback:
            on_edit_callback(mapping)

    def update_tree_data(mappings: dict[str, str]) -> None:
        # Clear all existing rows
        for item in tree.get_children():
            tree.delete(item)

        # Insert updated data
        for block, replacement in mappings.items():
            tree.insert("", "end", values=(block, replacement))

    def copy_value(event=None):
        """ appends first non empty string from selected rows to clipboard. if all are empty, appends '' """
        selected_items = tree.selection()
        values = []
        for row in selected_items:
            value = tree.set(row, "replacement")
            if value == "":
                continue
            values.append(value)
        if len(values) == 0:
            values = [""]
        tree.clipboard_clear()
        tree.clipboard_append(values[0])

    def delete_value(event=None):
        """deletes values from all selected rows"""
        selected_items = tree.selection()
        pasted = tree.clipboard_get()
        for row in selected_items:
            try:
                tree.set(row, "replacement", "")
            except tk.TclError:
                pass
    def paste_value(event=None):
        """paste current clipboard to all selected rows"""
        selected_items = tree.selection()
        pasted = tree.clipboard_get()
        for row in selected_items:
            try:
                tree.set(row, "replacement", pasted)
            except tk.TclError:
                pass

    tree.heading("original", text="Original Block")
    tree.heading("replacement", text="Replacement Block")
    tree.column("original", width=350)
    tree.column("replacement", width=330)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for block, replacement in block_entries.items():
        tree.insert("", "end", values=(block, replacement))

    tree.bind("<Double-1>", on_double_click)

    # copy paste bulk
    tree.bind("<Control-c>", copy_value)
    tree.bind("<Control-C>", copy_value)
    tree.bind("<Control-v>", paste_value)
    tree.bind("<Control-V>", paste_value)

    tree.bind("<Delete>", delete_value)

    def select_all(event):
        tree.selection_set(tree.get_children())
        return "break"  # Prevent default behavior (like beeping or selecting text in widget)

    tree.bind("<Control-a>", select_all)
    tree.bind("<Control-A>", select_all)  # Handle both lowercase and uppercase

    tk.Button(frame, text="Replace blocks", command=on_run_callback).pack(pady=5)

    frame.pack(fill=tk.BOTH, expand=True)
    return [update_tree_data, get_current_mappings]


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main App Window")
    root.geometry("800x500")

    # Create a frame to hold the block mapping table
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


    def edit_callback(mapping: dict[str, str]):
        for key, value in mapping.items():
            print(f"{key} -> {value}")


    original_blocks = {
        "minecraft:stone": "",
        "minecraft:glass": "minecraft:air",
        "minecraft:oak_log[axis=y]": "",
        "minecraft:grass_block": "",
        "minecraft:dirt": "",
        "minecraft:cobblestone": "",
        "minecraft:sand": "",
        "minecraft:gravel": "",
        "minecraft:oak_leaves": "",
        "minecraft:birch_log": "",
        "minecraft:spruce_log": "",
        "minecraft:jungle_log": "",
        "minecraft:acacia_log": "",
        "minecraft:dark_oak_log": "",
        "minecraft:sandstone": "",
        "minecraft:red_sandstone": "",
        "minecraft:brick_block": "",
        "minecraft:tnt": "",
        "minecraft:bookshelf": "",
        "minecraft:mossy_cobblestone": "",
        "minecraft:obsidian": "",
        "minecraft:diamond_ore": "",
        "minecraft:iron_ore": "",
        "minecraft:coal_ore": "",
        "minecraft:gold_ore": "",
        "minecraft:redstone_ore": "",
        "minecraft:lapis_ore": "",
        "minecraft:emerald_ore": "",
        "minecraft:nether_quartz_ore": "",
        "minecraft:netherrack": "",
        "minecraft:soul_sand": "",
        "minecraft:glowstone": "",
        "minecraft:nether_brick": "",
        "minecraft:end_stone": "",
        "minecraft:sea_lantern": "",
        "minecraft:prismarine": "",
        "minecraft:prismarine_bricks": "",
        "minecraft:dark_prismarine": "",
        "minecraft:sponge": "",
        "minecraft:wet_sponge": "",
        "minecraft:clay": ""
    }
    # Suggestion list — ideally the full list of vanilla or custom blocks
    block_suggestions = [
        "minecraft:air", "minecraft:stone", "minecraft:dirt", "minecraft:glass",
        "minecraft:grass_block", "minecraft:sand", "minecraft:gravel",
        "minecraft:oak_log", "minecraft:stripped_oak_log", "minecraft:log",
        "minecraft:oak_planks", "minecraft:iron_block"
    ]
    block_suggestions.sort()

    block_mapping_table(frame, original_blocks, block_suggestions, on_edit_callback=edit_callback)
    root.mainloop()
