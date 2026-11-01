import unittest
from autorod.domain.models.image_payload import ImagePayload, PixelFormat


class TestImagePayload(unittest.TestCase):

    def test_payload_validation_success(self) -> None:
        data = b'\x00' * 12
        payload = ImagePayload(
            width=2,
            height=2,
            pixel_format=PixelFormat.BGR8,
            stride=6,
            data=data,
            frame_id=1,
            captured_at_ns=0,
            source_id="test"
        )
        self.assertEqual(payload.nbytes(), 12)
        self.assertEqual(payload.width, 2)
        self.assertEqual(payload.height, 2)

    def test_payload_validation_failure_short_buffer(self) -> None:
        with self.assertRaises(ValueError):
            ImagePayload(
                width=2,
                height=2,
                pixel_format=PixelFormat.BGR8,
                stride=6,
                data=b'\x00',
                frame_id=1,
                captured_at_ns=0,
                source_id="test"
            )

    def test_payload_validation_failure_negative_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            ImagePayload(
                width=-1,
                height=2,
                pixel_format=PixelFormat.BGR8,
                stride=6,
                data=b'\x00' * 12,
                frame_id=1,
                captured_at_ns=0,
                source_id="test"
            )

    def test_payload_memoryview_becomes_readonly(self) -> None:
        mutable_buf = bytearray(b'\x01' * 12)
        mv = memoryview(mutable_buf)
        self.assertFalse(mv.readonly)

        payload = ImagePayload(
            width=2,
            height=2,
            pixel_format=PixelFormat.BGR8,
            stride=6,
            data=mv,
            frame_id=1,
            captured_at_ns=0,
            source_id="test"
        )
        self.assertTrue(isinstance(payload.data, memoryview))
        self.assertTrue(payload.data.readonly)


if __name__ == "__main__":
    unittest.main()
