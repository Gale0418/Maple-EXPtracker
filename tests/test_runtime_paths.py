import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "Maple-EXPtracker"
sys.path.insert(0, str(ROOT))

from runtime_paths import ASSETS_DIR, resolve_asset_path, select_tesseract_cmd


class RuntimePathTests(unittest.TestCase):
    def test_asset_paths_resolve_relative_to_module_directory(self):
        exp_asset = Path(resolve_asset_path("EXP.png"))
        login_asset = Path(resolve_asset_path("login.png"))
        self.assertEqual(exp_asset.parent, ASSETS_DIR.resolve())
        self.assertTrue(exp_asset.is_file())
        self.assertTrue(login_asset.is_file())

    def test_env_override_wins_for_tesseract(self):
        env = dict(os.environ)
        env["TESSERACT_CMD"] = r"D:\Tools\tesseract.exe"
        self.assertEqual(select_tesseract_cmd(env=env, candidates=()), r"D:\Tools\tesseract.exe")

    def test_missing_candidates_returns_none_without_override(self):
        env = dict(os.environ)
        env.pop("TESSERACT_CMD", None)
        self.assertIsNone(select_tesseract_cmd(env=env, candidates=()))


if __name__ == "__main__":
    unittest.main()
