import unittest
import main


class TestLoudPack(unittest.TestCase):
    def setUp(self):
        # Disable logging output during tests to keep the console clean
        import logging

        logging.disable(logging.CRITICAL)

    def tearDown(self):
        import logging

        logging.disable(logging.NOTSET)

    def test_resolve_version_metadata_url_exact(self):
        """Test resolving an exact version ID."""
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
        """Test resolving the 'latest' alias."""
        manifest = {
            "latest": {"release": "1.20.4", "snapshot": "24w14a"},
            "versions": [{"id": "1.20.4", "url": "http://example.com/1.20.4.json"}],
        }
        url = main.resolve_version_metadata_url("latest", manifest)
        self.assertEqual(url, "http://example.com/1.20.4.json")

    def test_resolve_version_metadata_url_snapshot(self):
        """Test resolving the 'snapshot' alias."""
        manifest = {
            "latest": {"release": "1.20.4", "snapshot": "24w14a"},
            "versions": [{"id": "24w14a", "url": "http://example.com/24w14a.json"}],
        }
        url = main.resolve_version_metadata_url("snapshot", manifest)
        self.assertEqual(url, "http://example.com/24w14a.json")

    def test_resolve_version_metadata_url_not_found(self):
        """Test behavior when a version is not in the manifest."""
        manifest = {
            "latest": {"release": "1.20.4", "snapshot": "24w14a"},
            "versions": [{"id": "1.20.4", "url": "http://example.com/1.20.4.json"}],
        }
        with self.assertRaises(SystemExit) as cm:
            main.resolve_version_metadata_url("1.19", manifest)
        self.assertEqual(cm.exception.code, 1)

    def test_filter_sound_assets(self):
        """Test filtering out non-sound assets."""
        asset_objects = {
            "minecraft/sounds/mob/cow.ogg": {"hash": "abc1234"},
            "minecraft/textures/block/stone.png": {"hash": "def5678"},
            "minecraft/sounds/music/game.ogg": {"hash": "ghi9012"},
            "minecraft/lang/en_us.json": {"hash": "jkl3456"},
        }
        filtered = main.filter_sound_assets(asset_objects)

        self.assertEqual(len(filtered), 2)
        self.assertIn("minecraft/sounds/mob/cow.ogg", filtered)
        self.assertIn("minecraft/sounds/music/game.ogg", filtered)
        self.assertNotIn("minecraft/textures/block/stone.png", filtered)
        self.assertEqual(filtered["minecraft/sounds/mob/cow.ogg"], "abc1234")


if __name__ == "__main__":
    unittest.main()
