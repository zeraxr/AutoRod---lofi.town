"""Pruebas unitarias para el comprobador de versiones semánticas y actualizaciones."""

import unittest
from autorod.infrastructure.updater.github_checker import (
    _parse_version_tuple,
    UpdateInfo
)


class TestUpdateChecker(unittest.TestCase):

    def test_parse_version_tuple(self) -> None:
        self.assertEqual(_parse_version_tuple("v2.0.0"), (2, 0, 0))
        self.assertEqual(_parse_version_tuple("2.1.5"), (2, 1, 5))
        self.assertEqual(_parse_version_tuple("v3.0.0-rc1"), (3, 0, 0, 1))

    def test_semver_comparisons(self) -> None:
        v_current = _parse_version_tuple("2.0.0")
        v_newer = _parse_version_tuple("v2.1.0")
        v_older = _parse_version_tuple("v1.9.9")
        v_equal = _parse_version_tuple("2.0.0")

        self.assertGreater(v_newer, v_current)
        self.assertLess(v_older, v_current)
        self.assertEqual(v_equal, v_current)

    def test_update_info_dataclass(self) -> None:
        info = UpdateInfo(
            has_update=True,
            latest_version="v2.1.0",
            current_version="2.0.0",
            release_name="AutoRod v2.1.0",
            release_notes="Mejoras visuales",
            html_url="https://github.com/zeraxr/AutoRod/releases/v2.1.0",
            download_url="https://github.com/zeraxr/AutoRod/releases/download/v2.1.0/Setup.exe"
        )
        self.assertTrue(info.has_update)
        self.assertEqual(info.latest_version, "v2.1.0")


if __name__ == "__main__":
    unittest.main()
