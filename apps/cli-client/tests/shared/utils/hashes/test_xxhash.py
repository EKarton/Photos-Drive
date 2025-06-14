import unittest
import tempfile
import os
import xxhash

from photos_drive.shared.utils.hashes.xxhash import compute_file_hash


class TestComputeFileHash(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file_path = self.temp_file.name

    def tearDown(self):
        os.unlink(self.temp_file_path)

    def test_empty_file(self):
        with open(self.temp_file_path, 'w'):
            pass

        self.assertEqual(
            compute_file_hash(self.temp_file_path), xxhash.xxh64().digest()
        )

    def test_small_file(self):
        content = b"Hello, World!"
        with open(self.temp_file_path, 'wb') as f:
            f.write(content)

        self.assertEqual(
            compute_file_hash(self.temp_file_path), xxhash.xxh64(content).digest()
        )

    def test_large_file(self):
        content = b"A" * 1000000  # 1MB of data
        with open(self.temp_file_path, 'wb') as f:
            f.write(content)

        self.assertEqual(
            compute_file_hash(self.temp_file_path), xxhash.xxh64(content).digest()
        )

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            compute_file_hash("non_existent_file.txt")

    def test_return_type(self):
        with open(self.temp_file_path, 'w') as f:
            f.write("Test")

        result = compute_file_hash(self.temp_file_path)

        # xxh64 produces a 64-bit (8-byte) hash, which is 16 characters in hex
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 8)

    def test_returns_same_file_hash(self):
        content = b"Known test content"
        with open(self.temp_file_path, 'wb') as f:
            f.write(content)

        computed_hash = compute_file_hash(self.temp_file_path)

        self.assertEqual(computed_hash, b'\x8a\x19\xdd\xdeg\xdd\x96\xf2')
