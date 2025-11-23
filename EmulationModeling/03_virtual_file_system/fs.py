import json
import pickle
import os
from fs_nodes import Directory, File

class VirtualFileSystem:
    def __init__(self):
        self.root = Directory("/")
        self.current_dir = self.root

    def _resolve_path(self, path):
        if path == "/":
            return self.root

        parts = path.strip("/").split("/")
        node = self.root if path.startswith("/") else self.current_dir

        for part in parts:
            if part == "." or part == "":
                continue
            elif part == "..":
                if node.parent:
                    node = node.parent
            else:
                if isinstance(node, Directory) and part in node.children:
                    node = node.get_child(part)
                else:
                    return None
        return node

    def mkdir(self, path):
        if "/" in path:
            parent_path, name = path.rsplit("/", 1)
            parent = self._resolve_path(parent_path if parent_path else "/")
        else:
            parent = self.current_dir
            name = path

        if parent and isinstance(parent, Directory):
            if name in parent.children:
                return f"Error: '{name}' already exists."
            new_dir = Directory(name, parent=parent)
            parent.add_child(new_dir)
            return f"Directory '{name}' created."
        return "Error: Invalid path."

    def touch(self, path, content=""):
        if "/" in path:
            parent_path, name = path.rsplit("/", 1)
            parent = self._resolve_path(parent_path if parent_path else "/")
        else:
            parent = self.current_dir
            name = path

        if parent and isinstance(parent, Directory):
            if name in parent.children:
                node = parent.get_child(name)
                if isinstance(node, File):
                    node.write(content)
                    return f"File '{name}' updated."
                return f"Error: '{name}' is a directory."
            new_file = File(name, content, parent=parent)
            parent.add_child(new_file)
            return f"File '{name}' created."
        return "Error: Invalid path."

    def ls(self, path=None):
        target = self.current_dir
        if path:
            target = self._resolve_path(path)

        if target and isinstance(target, Directory):
            return "\n".join([f"{name}{'/' if target.children[name].is_dir else ''}" for name in target.children])
        elif target:
            return target.name
        return "Error: Path not found."

    def cd(self, path):
        target = self._resolve_path(path)
        if target and isinstance(target, Directory):
            self.current_dir = target
            return ""
        return "Error: Invalid directory."

    def pwd(self):
        path = []
        curr = self.current_dir
        while curr != self.root:
            path.append(curr.name)
            curr = curr.parent
        return "/" + "/".join(reversed(path))

    def cat(self, path):
        target = self._resolve_path(path)
        if target and isinstance(target, File):
            return target.read()
        return "Error: File not found or is a directory."

    def rm(self, path):
        if "/" in path:
            parent_path, name = path.rsplit("/", 1)
            parent = self._resolve_path(parent_path if parent_path else "/")
        else:
            parent = self.current_dir
            name = path

        if parent and isinstance(parent, Directory):
            if parent.remove_child(name):
                return f"'{name}' removed."
        return "Error: Failed to remove."

    def save_state(self, filepath):
        try:
            # Recursive dict generation
            data = self.root.to_dict()
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            return "File system saved."
        except Exception as e:
            return f"Error saving: {e}"

    def load_state(self, filepath):
        if not os.path.exists(filepath):
            return "Error: Save file not found."
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.root = self._reconstruct_from_dict(data)
            self.current_dir = self.root
            return "File system loaded."
        except Exception as e:
            return f"Error loading: {e}"

    def _reconstruct_from_dict(self, data, parent=None):
        if data["is_dir"]:
            node = Directory(data["name"], parent=parent)
            for child_data in data["children"]:
                child_node = self._reconstruct_from_dict(child_data, parent=node)
                node.children[child_node.name] = child_node
        else:
            node = File(data["name"], data["content"], parent=parent)

        node.created_at = data["created_at"]
        node.modified_at = data["modified_at"]
        node.permissions = data["permissions"]
        return node
