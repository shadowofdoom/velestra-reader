import os
import tempfile
import unittest
from pathlib import Path

from velestra_reader.config import load_config


class TestConfig(unittest.TestCase):
    def test_loads_oauth_values_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.env"
            config_path.write_text(
                "\n".join(
                    [
                        "VELESTRA_READER_AUTH=oauth",
                        "VELESTRA_READER_CLIENT_ID=file-client",
                        "VELESTRA_READER_CLIENT_SECRET=file-secret",
                        "VELESTRA_READER_USER_AGENT=script:velestra-reader:0.1.0 (by /u/example)",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_config(
                environ={"VELESTRA_READER_CONFIG": str(config_path)}
            )

            self.assertEqual(config.auth_mode, "oauth")
            self.assertEqual(config.client_id, "file-client")
            self.assertEqual(config.client_secret, "file-secret")
            self.assertEqual(
                config.user_agent,
                "script:velestra-reader:0.1.0 (by /u/example)",
            )

    def test_environment_values_override_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.env"
            config_path.write_text(
                "\n".join(
                    [
                        "VELESTRA_READER_AUTH=oauth",
                        "VELESTRA_READER_CLIENT_ID=file-client",
                        "VELESTRA_READER_CLIENT_SECRET=file-secret",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_config(
                environ={
                    "VELESTRA_READER_CONFIG": str(config_path),
                    "VELESTRA_READER_CLIENT_ID": "env-client",
                }
            )

            self.assertEqual(config.client_id, "env-client")
            self.assertEqual(config.client_secret, "file-secret")

    def test_missing_default_config_file_is_allowed(self):
        config = load_config(environ={"VELESTRA_READER_CONFIG": os.devnull})

        self.assertEqual(config.auth_mode, "auto")
        self.assertIsNone(config.client_id)


if __name__ == "__main__":
    unittest.main()
