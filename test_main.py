import unittest
import tempfile
import subprocess
import zipfile
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
        mock_subprocess.return_value = MagicMock()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "raw" / "test.ogg"
            output_file = temp_path / "processed" / "test.ogg"

            input_file.parent.mkdir(parents=True)
            input_file.touch()

            result = main.process_single_audio(input_file, output_file, 2.0)

            self.assertTrue(result)
            mock_subprocess.assert_called_once()

    def test_package_resource_pack(self):
        """Test the zipping logic and structural enforcement of the resource pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            processed_dir = temp_path / "processed_assets"
            repo_root = temp_path / "repo"
            output_zip = temp_path / "output.zip"

            # Create dummy processed structure
            sound_dir = processed_dir / "minecraft" / "sounds"
            sound_dir.mkdir(parents=True)
            (sound_dir / "test.ogg").touch()

            # Create dummy metadata in fake repository root
            repo_root.mkdir()
            (repo_root / "pack.mcmeta").write_text('{"pack":{}}')
            (repo_root / "pack.png").touch()

            # Run packaging
            result = main.package_resource_pack(processed_dir, output_zip, repo_root)

            self.assertTrue(result)
            self.assertTrue(output_zip.exists())

            # Verify zip contents are mapped properly
            with zipfile.ZipFile(output_zip, "r") as zipf:
                namelist = zipf.namelist()
                self.assertIn("assets/minecraft/sounds/test.ogg", namelist)
                self.assertIn("pack.mcmeta", namelist)
                self.assertIn("pack.png", namelist)


if __name__ == "__main__":
    unittest.main()
