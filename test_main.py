import unittest
import tempfile
import subprocess
import zipfile
import json
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
        version, url = main.resolve_version_metadata_url("1.20.4", manifest)
        self.assertEqual(version, "1.20.4")
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

            result = main.process_single_audio(input_file, output_file, 20.0)
            self.assertTrue(result)
            mock_subprocess.assert_called_once()

    def test_package_resource_pack(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            processed_dir = temp_path / "processed_assets"
            repo_root = temp_path / "repo"
            output_zip = temp_path / "output.zip"

            sound_dir = processed_dir / "minecraft" / "sounds"
            sound_dir.mkdir(parents=True)
            (sound_dir / "test.ogg").touch()

            repo_root.mkdir()
            (repo_root / "pack.mcmeta").write_text('{"pack":{}}')

            result = main.package_resource_pack(processed_dir, output_zip, repo_root)
            self.assertTrue(result)
            self.assertTrue(output_zip.exists())

    @patch("main.requests.post")
    def test_upload_to_modrinth(self, mock_post):
        """Test the multipart form data generation for Modrinth API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "dummy_version_id"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix=".zip") as dummy_zip:
            dummy_path = Path(dummy_zip.name)

            # Test a release version
            result = main.upload_to_modrinth(
                dummy_path, "1.20.4", "my_proj", "fake_token"
            )

            self.assertEqual(
                result, "https://modrinth.com/project/my_proj/version/dummy_version_id"
            )

            # Verify the call arguments
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args

            self.assertEqual(kwargs["headers"], {"Authorization": "fake_token"})

            # Verify the embedded JSON payload
            sent_data = json.loads(kwargs["data"]["data"])
            self.assertEqual(sent_data["version_number"], "1.20.4")
            self.assertEqual(sent_data["version_type"], "release")
            self.assertEqual(sent_data["project_id"], "my_proj")
            self.assertIn("file", kwargs["files"])

    @patch("main.requests.post")
    def test_upload_to_modrinth_snapshot(self, mock_post):
        """Test that snapshot formats ('w' in name) correctly map to 'alpha' version type."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "dummy_version_id"}
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix=".zip") as dummy_zip:
            main.upload_to_modrinth(
                Path(dummy_zip.name), "24w14a", "my_proj", "fake_token"
            )

            args, kwargs = mock_post.call_args
            sent_data = json.loads(kwargs["data"]["data"])
            self.assertEqual(sent_data["version_type"], "alpha")


if __name__ == "__main__":
    unittest.main()
