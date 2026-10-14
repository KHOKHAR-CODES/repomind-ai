import tempfile
import unittest
from pathlib import Path
from app.services.repo_loader import ALLOWED_EXTENSIONS, EXCLUDED_DIRS, scan_repository

class RepoLoaderTests(unittest.TestCase):
    def test_strict_allowlist_and_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
            (root / "src" / "picture.png").write_bytes(b"not source")
            (root / "src" / "binary.py").write_bytes(b"\x00\x01\xff")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "bad.py").write_text("ignored", encoding="utf-8")
            result = scan_repository(root)
            self.assertEqual(result.file_count, 1)
            self.assertEqual(result.files[0].relative_path, "src/main.py")
            self.assertGreaterEqual(result.skipped.get("excluded_directory", 0), 1)
            self.assertIn(".py", ALLOWED_EXTENSIONS)
            self.assertIn("node_modules", EXCLUDED_DIRS)

    def test_invalid_utf8_is_ignored_and_large_file_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "weird.py").write_bytes(b"print('ok')\xff\n")
            (root / "large.py").write_text("x" * 100, encoding="utf-8")
            result = scan_repository(root, max_file_bytes=64)
            self.assertEqual(result.file_count, 1)
            self.assertIn("print('ok')", result.files[0].content)
            self.assertEqual(result.skipped.get("oversized"), 1)

if __name__ == "__main__":
    unittest.main()
