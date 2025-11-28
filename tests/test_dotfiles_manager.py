import os
import shutil
import tempfile
import unittest

from Practical.DotfilesManager.__main__ import install_dotfiles


class TestDotfilesManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, "dotfiles")
        self.home_dir = os.path.join(self.test_dir, "home")

        os.makedirs(self.source_dir)
        os.makedirs(self.home_dir)

        # Create a source dotfile (without dot)
        with open(os.path.join(self.source_dir, "vimrc"), "w") as f:
            f.write("syntax on")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_install_dotfiles(self):
        install_dotfiles(self.source_dir, self.home_dir)

        target_path = os.path.join(self.home_dir, ".vimrc")
        self.assertTrue(os.path.islink(target_path))
        self.assertEqual(
            os.readlink(target_path), os.path.join(self.source_dir, "vimrc")
        )

    def test_backup_existing(self):
        # Create existing file in home
        target_path = os.path.join(self.home_dir, ".vimrc")
        with open(target_path, "w") as f:
            f.write("old config")

        install_dotfiles(self.source_dir, self.home_dir, backup=True)

        # Check link creation
        self.assertTrue(os.path.islink(target_path))

        # Check backup existence
        self.assertTrue(os.path.exists(target_path + ".bak"))
        with open(target_path + ".bak", "r") as f:
            self.assertEqual(f.read(), "old config")

    def test_dry_run(self):
        install_dotfiles(self.source_dir, self.home_dir, dry_run=True)
        target_path = os.path.join(self.home_dir, ".vimrc")
        self.assertFalse(os.path.exists(target_path))


if __name__ == "__main__":
    unittest.main()
