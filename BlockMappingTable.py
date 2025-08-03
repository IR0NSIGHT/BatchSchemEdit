import tkinter as tk
from tkinter import ttk


class AutocompleteEntry(tk.Entry):
    def __init__(self, master, suggestions, **kwargs):
        super().__init__(master, **kwargs)
        self.suggestions = suggestions
        self.listbox = None
        self.bind("<KeyRelease>", self.on_key_release)

    def on_key_release(self, event):
        value = self.get()
        if not value:
            self.hide_suggestions()
            return

        filtered = [s for s in self.suggestions if s.startswith(value)]
        if filtered:
            if not self.listbox:
                self.show_suggestions()
            self.update_listbox(filtered)
        else:
            self.hide_suggestions()

    def show_suggestions(self):
        self.listbox = tk.Listbox(self.master, height=6)
        self.listbox.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
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
                        on_edit_callback=None):
    """
    table component with two columns: original, replacement.
    :param parent: Tk widget (frame/window) to insert the table into
    :param block_entries: dict of original -> replacement blocks
    :param suggestion_blocks: list of strings for autocomplete suggestions
    :param on_edit_callback: function to call with current mapping on button press
    :return: the frame containing the table and controls
    """

    frame = tk.Frame(parent)

    def on_double_click(event):
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)

        if column != '#2' or not row_id:
            return

        x, y, width, height = tree.bbox(row_id, column=column)
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
        mapping = {}
        for row in tree.get_children():
            values = tree.item(row, "values")
            key = values[0]
            value = values[1]
            if value == "":
                continue
            mapping[key] = value
        if on_edit_callback:
            on_edit_callback(mapping)

    tree = ttk.Treeview(frame, columns=("original", "replacement"), show="headings")
    tree.heading("original", text="Original Block")
    tree.heading("replacement", text="Replacement Block")
    tree.column("original", width=350)
    tree.column("replacement", width=330)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for block, replacement in block_entries.items():
        tree.insert("", "end", values=(block, replacement))

    tree.bind("<Double-1>", on_double_click)

    tk.Button(frame, text="Submit", command=on_run_callback).pack(pady=5)

    frame.pack(fill=tk.BOTH, expand=True)
    return frame


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
        "minecraft:grass_block": ""
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
