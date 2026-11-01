import unittest
from autorod.infrastructure.templates.file_repository import FileTemplateRepository
from autorod.domain.errors import TemplateNotFoundError
from autorod.domain.models.image_payload import ImagePayload, PixelFormat


class TestFileTemplateRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.repo = FileTemplateRepository()

    def test_list_templates_finds_official_buttons(self) -> None:
        templates = self.repo.list_templates()
        self.assertIn("cast_button", templates)
        self.assertIn("reel_button", templates)

    def test_load_cast_button_returns_valid_payload(self) -> None:
        payload = self.repo.load("cast_button")
        self.assertIsInstance(payload, ImagePayload)
        self.assertEqual(payload.width, 114)
        self.assertEqual(payload.height, 60)
        self.assertEqual(payload.pixel_format, PixelFormat.BGR8)
        self.assertGreater(len(payload.data), 0)

    def test_load_reel_button_returns_valid_payload(self) -> None:
        payload = self.repo.load("reel_button")
        self.assertIsInstance(payload, ImagePayload)
        self.assertEqual(payload.width, 114)
        self.assertEqual(payload.height, 60)
        self.assertEqual(payload.pixel_format, PixelFormat.BGR8)

    def test_load_uses_memory_cache(self) -> None:
        p1 = self.repo.load("cast_button")
        p2 = self.repo.load("cast_button")
        self.assertIs(p1, p2)

    def test_load_non_existent_template_raises_template_not_found(self) -> None:
        with self.assertRaises(TemplateNotFoundError):
            self.repo.load("non_existent_button_xyz")


if __name__ == "__main__":
    unittest.main()
