import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from Practical.MediaLibraryOrganizer.__main__ import organize_library, clean_filename

class TestMediaOrganizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, "source")
        self.target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(self.source_dir)

        # Create dummy movie file
        self.dummy_file = os.path.join(self.source_dir, "The.Matrix.1999.1080p.mp4")
        with open(self.dummy_file, 'w') as f:
            f.write("dummy content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_clean_filename(self):
        name, year = clean_filename("The.Matrix.1999.1080p.mp4")
        self.assertEqual(name, "The Matrix")
        self.assertEqual(year, "1999")

        name, year = clean_filename("Inception.2010.mkv")
        self.assertEqual(name, "Inception")
        self.assertEqual(year, "2010")

    @patch("Practical.MediaLibraryOrganizer.__main__.requests.get")
    def test_organize_library(self, mock_get):
        # Mock TMDB response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "title": "The Matrix",
                    "release_date": "1999-03-30"
                }
            ]
        }
        mock_get.return_value = mock_resp

        organize_library(self.source_dir, self.target_dir, "fake_key")

        expected_path = os.path.join(self.target_dir, "The Matrix (1999)", "The Matrix (1999).mp4")
        self.assertTrue(os.path.exists(expected_path))

if __name__ == "__main__":
    unittest.main()
