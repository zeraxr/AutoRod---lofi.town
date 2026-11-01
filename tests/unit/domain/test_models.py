import unittest
from autorod.domain.models.geometry import Point, Size, Region
from autorod.domain.models.match_result import MatchResult
from autorod.domain.models.diagnostics import DiagnosticFrame
from autorod.domain.models.image_payload import ImagePayload, PixelFormat


class TestDomainModels(unittest.TestCase):

    def test_geometry_immutability(self) -> None:
        p = Point(x=10, y=20)
        s = Size(width=100, height=200)
        r = Region(top_left=p, size=s)

        self.assertEqual(r.top_left.x, 10)
        self.assertEqual(r.size.width, 100)

        with self.assertRaises(AttributeError):
            p.x = 99  # type: ignore

    def test_size_negative_dimensions_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Size(width=-5, height=10)

    def test_match_result_confidence_bounds(self) -> None:
        mr = MatchResult(
            found=True,
            confidence=0.85,
            region=None,
            center=Point(x=5, y=5),
            strategy_id="test",
            frame_id=1
        )
        self.assertTrue(mr.found)

        with self.assertRaises(ValueError):
            MatchResult(
                found=True,
                confidence=1.5,
                region=None,
                center=None,
                strategy_id="test",
                frame_id=1
            )

    def test_diagnostic_frame_deep_immutability(self) -> None:
        payload = ImagePayload(
            width=1, height=1, pixel_format=PixelFormat.GRAY8,
            stride=1, data=b'\x00', frame_id=1, captured_at_ns=0, source_id="test"
        )
        mutable_boxes = [Region(top_left=Point(x=0, y=0), size=Size(width=1, height=1))]
        df = DiagnosticFrame(
            payload=payload,
            layer_name="test_layer",
            bounding_boxes=mutable_boxes
        )

        self.assertIsInstance(df.bounding_boxes, tuple)
        # Mutating the original list does not mutate df.bounding_boxes
        mutable_boxes.clear()
        self.assertEqual(len(df.bounding_boxes), 1)


if __name__ == "__main__":
    unittest.main()
