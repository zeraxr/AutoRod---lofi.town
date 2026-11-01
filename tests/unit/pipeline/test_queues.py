import unittest
from autorod.application.pipeline.queues import LatestFrameQueue, _STOP


class TestLatestFrameQueue(unittest.TestCase):

    def test_put_and_get(self) -> None:
        q: LatestFrameQueue[str] = LatestFrameQueue(maxsize=1)
        q.put_latest("frame_1")
        item = q.get(timeout=0.1)
        self.assertEqual(item, "frame_1")
        self.assertEqual(q.dropped_count, 0)

    def test_latest_frame_wins_policy(self) -> None:
        q: LatestFrameQueue[str] = LatestFrameQueue(maxsize=1)
        q.put_latest("frame_1")
        q.put_latest("frame_2")
        q.put_latest("frame_3")

        item = q.get(timeout=0.1)
        self.assertEqual(item, "frame_3")
        self.assertEqual(q.dropped_count, 2)

    def test_sentinel_passed_correctly(self) -> None:
        q: LatestFrameQueue[object] = LatestFrameQueue(maxsize=1)
        q.put_latest(_STOP)
        item = q.get(timeout=0.1)
        self.assertIs(item, _STOP)


if __name__ == "__main__":
    unittest.main()
