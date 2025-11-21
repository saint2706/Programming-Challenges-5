import unittest
import os
import shutil
import tempfile
from Practical.StaticSiteGenerator.__main__ import StaticSiteGenerator

class TestStaticSiteGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")

        os.makedirs(os.path.join(self.input_dir, "content"))
        os.makedirs(os.path.join(self.input_dir, "templates"))
        os.makedirs(os.path.join(self.input_dir, "static"))

        # Create a template
        with open(os.path.join(self.input_dir, "templates", "post.html"), "w") as f:
            f.write("<html><h1>{{ post.meta.title }}</h1>{{ post.content }}</html>")

        with open(os.path.join(self.input_dir, "templates", "index.html"), "w") as f:
            f.write("<ul>{% for p in posts %}<li>{{ p.meta.title }}</li>{% endfor %}</ul>")

        # Create content
        with open(os.path.join(self.input_dir, "content", "hello.md"), "w") as f:
            f.write("title: Hello World\ndate: 2023-01-01\n\n# Hello\nThis is a test.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_build(self):
        generator = StaticSiteGenerator(self.input_dir, self.output_dir)
        generator.build()

        # Check output exists
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "hello.html")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "index.html")))

        # Check content
        with open(os.path.join(self.output_dir, "hello.html"), "r") as f:
            content = f.read()
            self.assertIn("Hello World", content)
            self.assertIn("This is a test", content)

        with open(os.path.join(self.output_dir, "index.html"), "r") as f:
            content = f.read()
            self.assertIn("Hello World", content)

if __name__ == "__main__":
    unittest.main()
