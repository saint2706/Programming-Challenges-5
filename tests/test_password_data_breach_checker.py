import unittest
from unittest.mock import MagicMock, patch

from Practical.PasswordDataBreachChecker.__main__ import check_password


class TestPasswordChecker(unittest.TestCase):

    @patch("Practical.PasswordDataBreachChecker.__main__.requests.get")
    def test_check_password_found(self, mock_get):
        # Mock response for hash of 'password' (5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8)
        # Prefix: 5BAA6
        # Suffix: 1E4C9B93F3F0682250B6CF8331B7EE68FD8

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Return a list including the matching suffix
        mock_resp.text = "00000000000000000000000000000000000:1\n1E4C9B93F3F0682250B6CF8331B7EE68FD8:1000\n"
        mock_get.return_value = mock_resp

        count = check_password("password")
        self.assertEqual(count, 1000)

        # Verify correct prefix sent
        mock_get.assert_called_with("https://api.pwnedpasswords.com/range/5BAA6")

    @patch("Practical.PasswordDataBreachChecker.__main__.requests.get")
    def test_check_password_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "00000000000000000000000000000000000:1\n"
        mock_get.return_value = mock_resp

        count = check_password("super_unique_password_that_hopefully_isnt_pwned")
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
