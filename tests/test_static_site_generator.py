import shutil
import tempfile
import unittest
from pathlib import Path

from Practical.static_site_generator.generator import SiteGenerator


class TestStaticSiteGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.test_dir) / "input"
        self.output_dir = Path(self.test_dir) / "output"

        (self.input_dir / "content").mkdir(parents=True)
        (self.input_dir / "templates").mkdir(parents=True)
        (self.input_dir / "static").mkdir(parents=True)

        # Create a base template
        with open(self.input_dir / "templates" / "base.html", "w") as f:
            f.write(
                "<html><head><title>{{ meta.title }}</title></head><body>{{ content }}</body></html>"
            )

        # Create content with proper frontmatter (uses --- delimiters)
        with open(self.input_dir / "content" / "hello.md", "w") as f:
            f.write(
                "---\ntitle: Hello World\ndate: 2023-01-01\n---\n# Hello\nThis is a test."
            )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_build(self):
        generator = SiteGenerator(self.input_dir, self.output_dir)
        generator.build()

        # Check output exists
        self.assertTrue((self.output_dir / "hello.html").exists())

        # Check content
        with open(self.output_dir / "hello.html", "r") as f:
            content = f.read()
            self.assertIn("Hello World", content)
            self.assertIn("This is a test", content)


if __name__ == "__main__":
    unittest.main()
