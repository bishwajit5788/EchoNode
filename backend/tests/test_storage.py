import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.storage import LocalStorageService

class TestStorageService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name)
        self.storage = LocalStorageService(storage_dir=self.storage_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_retrieve_file(self):
        # Create a mock audio file
        src_file = self.storage_dir / "temp_source.m4a"
        src_file.write_bytes(b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00isomiso2")

        url = self.storage.save_file("track_1.m4a", src_file, content_type="audio/mp4")
        self.assertEqual(url, "/api/download/track_1.m4a")

        self.assertTrue(self.storage.file_exists("track_1.m4a"))
        p = self.storage.get_file_path("track_1.m4a")
        self.assertIsNotNone(p)
        self.assertTrue(p.exists())

    def test_list_files(self):
        file1 = self.storage_dir / "ambient_rain.m4a"
        file1.write_bytes(b"data1")
        file2 = self.storage_dir / "piano_melody.mp3"
        file2.write_bytes(b"data2")
        # Non-audio file should be ignored
        file3 = self.storage_dir / "readme.txt"
        file3.write_bytes(b"ignore me")

        files = self.storage.list_files()
        self.assertEqual(len(files), 2)
        filenames = {f.filename for f in files}
        self.assertIn("ambient_rain.m4a", filenames)
        self.assertIn("piano_melody.mp3", filenames)

    def test_path_traversal_prevention(self):
        # Attempting path traversal should return None
        p = self.storage.get_file_path("../../etc/passwd")
        self.assertIsNone(p)

    def test_delete_file(self):
        f = self.storage_dir / "delete_me.m4a"
        f.write_bytes(b"temp")
        self.assertTrue(self.storage.file_exists("delete_me.m4a"))

        res = self.storage.delete_file("delete_me.m4a")
        self.assertTrue(res)
        self.assertFalse(self.storage.file_exists("delete_me.m4a"))

if __name__ == "__main__":
    unittest.main()
