#!/usr/bin/env python3
"""Unit tests for scripts/security.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402


class SecurityTests(unittest.TestCase):
    def test_safe_resolve_allows_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            child = root / "inbox" / "clip.mp4"
            child.parent.mkdir(parents=True, exist_ok=True)
            resolved = security.safe_resolve(child, [root / "inbox"])
            self.assertEqual(resolved, child)

    def test_safe_resolve_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            inbox = root / "inbox"
            inbox.mkdir()
            with self.assertRaises(security.SecurityError):
                security.safe_resolve(inbox / ".." / "secret.txt", [inbox])

    def test_safe_slug_sanitizes(self) -> None:
        self.assertEqual(security.safe_slug("My Video; rm -rf /!"), "my-video-rm-rf")
        self.assertEqual(security.safe_slug("   "), "video-project")

    def test_sanitize_caption_text(self) -> None:
        raw = "Hello\x00 world \u2014 test\nline"
        self.assertEqual(security.sanitize_caption_text(raw), "Hello world test line")

    def test_escape_ffmpeg_filter_path(self) -> None:
        p = Path("C:/xampp/htdocs/videditor/projects/demo/work/captions.srt")
        escaped = security.escape_ffmpeg_filter_path(p)
        self.assertNotIn("\n", escaped)
        self.assertIn("\\:", escaped)


if __name__ == "__main__":
    unittest.main()

