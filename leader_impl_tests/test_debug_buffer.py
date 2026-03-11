from __future__ import annotations

import unittest

from leader_impl.debug_buffer import DebugBuffer


class DebugBufferTests(unittest.TestCase):
    def test_cursor_and_limit(self) -> None:
        buf = DebugBuffer(max_size=10)
        for i in range(5):
            buf.append("stdout", f"line-{i}")

        items, next_cursor = buf.read(limit=2)
        self.assertEqual([item.message for item in items], ["line-3", "line-4"])
        self.assertEqual(next_cursor, "5")

        items2, next_cursor2 = buf.read(limit=10, cursor="2")
        self.assertEqual([item.message for item in items2], ["line-2", "line-3", "line-4"])
        self.assertEqual(next_cursor2, "5")

    def test_buffer_truncation(self) -> None:
        buf = DebugBuffer(max_size=3)
        for i in range(6):
            buf.append("stderr", f"err-{i}")
        items, _ = buf.read(limit=10, cursor="0")
        self.assertEqual([item.message for item in items], ["err-3", "err-4", "err-5"])


if __name__ == "__main__":
    unittest.main()

