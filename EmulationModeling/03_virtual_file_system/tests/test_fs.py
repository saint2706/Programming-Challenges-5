import os
import unittest

from fs import VirtualFileSystem


class TestVirtualFileSystem(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()

    def test_mkdir_and_ls(self):
        self.vfs.mkdir("docs")
        self.vfs.mkdir("photos")
        output = self.vfs.ls()
        self.assertIn("docs/", output)
        self.assertIn("photos/", output)

    def test_cd_and_pwd(self):
        self.vfs.mkdir("usr")
        self.vfs.cd("usr")
        self.assertEqual(self.vfs.pwd(), "/usr")

        self.vfs.mkdir("bin")
        self.vfs.cd("bin")
        self.assertEqual(self.vfs.pwd(), "/usr/bin")

        self.vfs.cd("..")
        self.assertEqual(self.vfs.pwd(), "/usr")

    def test_touch_and_cat(self):
        self.vfs.touch("notes.txt", "Hello World")
        content = self.vfs.cat("notes.txt")
        self.assertEqual(content, "Hello World")

        # Test overwrite
        self.vfs.touch("notes.txt", "New Content")
        self.assertEqual(self.vfs.cat("notes.txt"), "New Content")

    def test_rm(self):
        self.vfs.touch("temp.txt")
        self.assertIn("temp.txt", self.vfs.ls())
        self.vfs.rm("temp.txt")
        self.assertNotIn("temp.txt", self.vfs.ls())

    def test_persistence(self):
        self.vfs.mkdir("data")
        self.vfs.touch("data/config", "key=value")
        self.vfs.save_state("test_fs.json")

        new_vfs = VirtualFileSystem()
        new_vfs.load_state("test_fs.json")

        self.assertIn("data/", new_vfs.ls())
        self.assertEqual(new_vfs.cat("data/config"), "key=value")

        if os.path.exists("test_fs.json"):
            os.remove("test_fs.json")

    def test_nested_paths(self):
        self.vfs.mkdir("a")
        self.vfs.mkdir("a/b")
        self.vfs.touch("a/b/c.txt", "deep file")

        self.assertEqual(self.vfs.cat("a/b/c.txt"), "deep file")

        self.vfs.cd("a/b")
        self.assertEqual(self.vfs.cat("c.txt"), "deep file")


if __name__ == "__main__":
    unittest.main()
