import unittest
import tempfile
import subprocess
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

    def test_filter_sound_assets(self):
        asset_objects = {
            "minecraft/sounds/mob/cow.ogg": {"hash": "abc1234"},
            "minecraft/textures/block/stone.png": {"hash": "def5678"},
        }
        filtered = main.filter_sound_assets(asset_objects)
        self.assertEqual(len(filtered), 1)

    def test_get_asset_url(self):
        hash_val = "43c080fc851412b186b4cb4659bc7e39a3c9fef4"
        expected_url = f"https://resources.download.minecraft.net/43/{hash_val}"
        self.assertEqual(main.get_asset_url(hash_val), expected_url)

    @patch("main.subprocess.run")
    def test_process_single_audio_success(self, mock_subprocess):
        """Test audio processing logic (mocking the actual SoX call)."""
        mock_subprocess.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "raw" / "test.ogg"
            output_file = temp_path / "processed" / "test.ogg"

            input_file.parent.mkdir(parents=True)
            input_file.touch()

            result = main.process_single_audio(input_file, output_file, 2.0)

            self.assertTrue(result)
            mock_subprocess.assert_called_once_with(
                ["sox", "-v", "2.0", str(input_file), str(output_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

    @patch("main.subprocess.run")
    def test_process_single_audio_skip_existing(self, mock_subprocess):
        """Test that SoX is bypassed if the processed file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "raw" / "test.ogg"
            output_file = temp_path / "processed" / "test.ogg"

            output_file.parent.mkdir(parents=True)
            output_file.touch()  # Simulate existing output

            result = main.process_single_audio(input_file, output_file, 2.0)

            self.assertTrue(result)
            mock_subprocess.assert_not_called()


if __name__ == "__main__":
    unittest.main()
