import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import main


class TestLoudPack(unittest.TestCase):
    def setUp(self):
        import logging

        logging.disable(logging.CRITICAL)

    def tearDown(self):
        import logging

        logging.disable(logging.NOTSET)

    def test_resolve_version_metadata_url_exact(self):
        manifest = {
            "latest": {"release": "1.20.4", "snapshot": "24w14a"},
            "versions": [
                {"id": "1.20.4", "url": "http://example.com/1.20.4.json"},
                {"id": "24w14a", "url": "http://example.com/24w14a.json"},
            ],
        }
        url = main.resolve_version_metadata_url("1.20.4", manifest)
        self.assertEqual(url, "http://example.com/1.20.4.json")

    def test_resolve_version_metadata_url_latest(self):
        manifest = {
            "latest": {"release": "1.20.4", "snapshot": "24w14a"},
            "versions": [{"id": "1.20.4", "url": "http://example.com/1.20.4.json"}],
        }
        url = main.resolve_version_metadata_url("latest", manifest)
        self.assertEqual(url, "http://example.com/1.20.4.json")

    def test_filter_sound_assets(self):
        asset_objects = {
            "minecraft/sounds/mob/cow.ogg": {"hash": "abc1234"},
            "minecraft/textures/block/stone.png": {"hash": "def5678"},
        }
        filtered = main.filter_sound_assets(asset_objects)
        self.assertEqual(len(filtered), 1)
        self.assertIn("minecraft/sounds/mob/cow.ogg", filtered)

    def test_get_asset_url(self):
        """Test Mojang asset URL construction using the hash subfolder logic."""
        hash_val = "43c080fc851412b186b4cb4659bc7e39a3c9fef4"
        expected_url = f"https://resources.download.minecraft.net/43/{hash_val}"
        self.assertEqual(main.get_asset_url(hash_val), expected_url)

    def test_download_single_asset_skip_existing(self):
        """Test that the download function returns the path immediately if the file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_asset_path = "minecraft/sounds/test.ogg"
            target_file = temp_path / fake_asset_path

            # Create dummy file to simulate existing download
            target_file.parent.mkdir(parents=True)
            target_file.write_bytes(b"dummy audio data")

            # Call function
            result = main.download_single_asset(fake_asset_path, "fakehash", temp_path)

            # Result should be the path, meaning it skipped downloading
            self.assertEqual(result, target_file)

    @patch("main.requests.get")
    def test_download_single_asset_success(self, mock_get):
        """Test successful download and directory creation."""
        mock_response = MagicMock()
        mock_response.content = b"fake audio data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_asset_path = "minecraft/sounds/new.ogg"

            result = main.download_single_asset(
                fake_asset_path, "fakehash123", temp_path
            )

            self.assertIsNotNone(result)
            self.assertTrue(result.exists())
            self.assertEqual(result.read_bytes(), b"fake audio data")


if __name__ == "__main__":
    unittest.main()
