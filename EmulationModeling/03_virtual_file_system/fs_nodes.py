"""
Emulation/Modeling project implementation.
"""

import json
import time

class Node:
    """
    Docstring for Node.
    """
    def __init__(self, name, is_dir=False, parent=None):
        """
        Docstring for __init__.
        """
        self.name = name
        self.is_dir = is_dir
        self.parent = parent
        self.created_at = time.time()
        self.modified_at = time.time()
        self.permissions = "rwxr-xr-x" # Default unix-like

    def to_dict(self):
        """
        Docstring for to_dict.
        """
        return {
            "name": self.name,
            "is_dir": self.is_dir,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "permissions": self.permissions
        }

class File(Node):
    """
    Docstring for File.
    """
    def __init__(self, name, content="", parent=None):
        """
        Docstring for __init__.
        """
        super().__init__(name, is_dir=False, parent=parent)
        self.content = content
        self.size = len(content)

    def write(self, content):
        """
        Docstring for write.
        """
        self.content = content
        self.size = len(content)
        self.modified_at = time.time()

    def read(self):
        """
        Docstring for read.
        """
        return self.content

    def to_dict(self):
        """
        Docstring for to_dict.
        """
        d = super().to_dict()
        d["content"] = self.content
        d["size"] = self.size
        return d

class Directory(Node):
    """
    Docstring for Directory.
    """
    def __init__(self, name, parent=None):
        """
        Docstring for __init__.
        """
        super().__init__(name, is_dir=True, parent=parent)
        self.children = {} # Map name -> Node

    def add_child(self, node):
        """
        Docstring for add_child.
        """
        self.children[node.name] = node
        node.parent = self
        self.modified_at = time.time()

    def remove_child(self, name):
        """
        Docstring for remove_child.
        """
        if name in self.children:
            del self.children[name]
            self.modified_at = time.time()
            return True
        return False

    def get_child(self, name):
        """
        Docstring for get_child.
        """
        return self.children.get(name)

    def list_children(self):
        """
        Docstring for list_children.
        """
        return list(self.children.keys())

    def to_dict(self):
        """
        Docstring for to_dict.
        """
        d = super().to_dict()
        d["children"] = [child.to_dict() for child in self.children.values()]
        return d
