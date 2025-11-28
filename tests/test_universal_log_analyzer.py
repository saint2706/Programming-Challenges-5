import os
import tempfile
import unittest
from unittest.mock import patch

from Practical.UniversalLogAnalyzer.__main__ import analyze_logs, parse_log_line


class TestLogAnalyzer(unittest.TestCase):

    def test_parse_log_line_valid(self):
        line = '127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326'
        result = parse_log_line(line)
        self.assertIsNotNone(result)
        self.assertEqual(result["ip"], "127.0.0.1")
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["status"], "200")
        self.assertEqual(result["size"], 2326)
        self.assertEqual(result["timestamp"].hour, 13)

    def test_parse_log_line_invalid(self):
        line = "Invalid Log Line"
        result = parse_log_line(line)
        self.assertIsNone(result)

    def test_parse_log_line_dash_size(self):
        line = '127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /data HTTP/1.0" 304 -'
        result = parse_log_line(line)
        self.assertEqual(result["size"], 0)

    @patch("matplotlib.pyplot.savefig")
    def test_analyze_logs(self, mock_savefig):
        # Create a dummy log file
        content = (
            '127.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /page1 HTTP/1.0" 200 100\n'
            '127.0.0.1 - - [10/Oct/2000:14:55:36 -0700] "GET /page1 HTTP/1.0" 200 100\n'
            '127.0.0.1 - - [10/Oct/2000:14:56:36 -0700] "POST /page2 HTTP/1.0" 404 0\n'
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            output_img = "test_output.png"
            analyze_logs(tmp_path, output_img)

            # Check if savefig was called
            mock_savefig.assert_called_with(output_img)

        finally:
            os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
