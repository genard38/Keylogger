
import tkinter as tk
from tkinter import ttk
import os
from tkinter import messagebox



class FileTreeWidget:
    """Manage the file tree view component"""

    MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    # Windows 11 style icons
    ICON_FOLDER = "📁"
    ICON_FILE = "📄"

    def __init__(self, parent, file_manager):
        self.file_manager = file_manager
        self.file_tree_items = {}
        self.on_file_selected = None  # Callback for file selection
        self.on_file_deleted = None  # Callback for file deletion

        self._create_widget(parent)

    def _create_widget(self, parent):
        """Create the tree view widget"""
        # Frame for tree and scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            selectmode='browse',
            height=8
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Bind events
        self.tree.bind('<Double-Button-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

    def populate(self, filter_text=""):
        """Populate tree with log files"""
        # Remember expanded state
        expanded_items = self._get_expanded_items()

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_tree_items.clear()

        # Get organized files
        organized = self.file_manager.organize_files()

        # Populate tree
        for month in self.MONTH_ORDER:
            if month not in organized:
                continue

            if not self._matches_filter(month, organized[month], filter_text):
                continue

            # Create month node
            month_text = f"{self.ICON_FOLDER} {month}"
            was_expanded = month_text in expanded_items
            month_id = self.tree.insert("", "end", text=month_text, open=was_expanded)

            # Sort days numerically
            days = sorted(organized[month].keys(), key=lambda x: int(x))

            for day in days:
                # Create day node (using file icon for txt representation)
                day_text = f"{self.ICON_FILE} keylog_day_{day}.txt"
                was_day_expanded = day_text in expanded_items
                day_id = self.tree.insert(month_id, "end", text=day_text, open=was_day_expanded)

                # Sort years (newest first)
                years_files = sorted(organized[month][day], key=lambda x: x[0], reverse=True)

                for year, filepath in years_files:
                    display_text = f"{month} {day} {year}"
                    if filter_text and filter_text.lower() not in display_text.lower():
                        continue

                    # Create file node
                    file_id = self.tree.insert(
                        day_id,
                        "end",
                        text=f"{self.ICON_FILE} {year}",
                        tags=('file',)
                    )
                    self.file_tree_items[file_id] = filepath

    def _get_expanded_items(self):
        """Get list of currently expanded items"""
        expanded = set()
        for item in self.tree.get_children():
            if self.tree.item(item, 'open'):
                expanded.add(self.tree.item(item, 'text'))
            for child in self.tree.get_children(item):
                if self.tree.item(child, 'open'):
                    expanded.add(self.tree.item(child, 'text'))
        return expanded

    def _matches_filter(self, month, days_dict, filter_text):
        """Check if month/days match filter"""
        if not filter_text:
            return True
        if filter_text.lower() in month.lower():
            return True
        for day in days_dict:
            for year, _ in days_dict[day]:
                if filter_text.lower() in f"{month} {day} {year}".lower():
                    return True
        return False

    def _on_double_click(self, event):
        """Handle double-click to open file"""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        if item_id in self.file_tree_items:
            filepath = self.file_tree_items[item_id]
            if self.on_file_selected:
                self.on_file_selected(filepath)

    def _on_right_click(self, event):
        """Show context menu"""
        item_id = self.tree.identify_row(event.y)
        if not item_id or item_id not in self.file_tree_items:
            return

        self.tree.selection_set(item_id)

        # Create context menu
        context_menu = tk.Menu(self.tree, tearoff=0)
        context_menu.add_command(label="Open", command=lambda: self._on_double_click(None))
        context_menu.add_command(label="Delete", command=lambda: self._delete_file(item_id))
        context_menu.add_separator()
        context_menu.add_command(label="Refresh", command=self.populate)

        context_menu.post(event.x_root, event.y_root)

    def _delete_file(self, item_id):
        """Delete selected file"""
        if item_id not in self.file_tree_items:
            return

        filepath = self.file_tree_items[item_id]
        filename = os.path.basename(filepath)

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete:\n{filename}?\n\nThis cannot be undone."):
            try:
                self.file_manager.delete_file(filepath)
                messagebox.showinfo("Success", f"Deleted: {filename}")
                self.populate()
                if self.on_file_deleted:
                    self.on_file_deleted(filepath)
            except Exception as e:
                messagebox.showerror("Error", str(e))