import json
import tempfile
import unittest
from pathlib import Path

from spechemobot_dataset.make_manifest import build_manifest, load_records


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_session(self, name, records):
        session = self.root / name
        session.mkdir(parents=True)
        with (session / "metadata.jsonl").open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record) + "\n")

    def test_load_records_skips_blank_lines_and_missing_file(self):
        session = self.root / "session-a"
        session.mkdir()
        (session / "metadata.jsonl").write_text(
            '{"sample_id": "a"}\n\n{"sample_id": "b"}\n', encoding="utf-8")
        self.assertEqual(len(load_records(session)), 2)
        self.assertEqual(load_records(self.root / "missing"), [])

    def test_build_manifest_filters_empty_and_splits(self):
        self.write_session("session-a", [
            {"sample_id": "a1", "rgb": "rgb/a1.png"},
            {"sample_id": "a2", "thermal": "thermal/a2.png"},
            {"sample_id": "a3"},
        ])
        self.write_session("session-b", [
            {"sample_id": "b1", "rgb": "rgb/b1.png"},
        ])

        manifest = build_manifest(self.root, val_fraction=0.5, seed=3)

        self.assertEqual(manifest["count"], 3)
        self.assertEqual(manifest["sessions"], ["session-a", "session-b"])
        self.assertEqual(len(manifest["train"]), 1)
        self.assertEqual(len(manifest["val"]), 2)
        self.assertTrue(all(item.get("session") for item in manifest["train"] + manifest["val"]))

    def test_build_manifest_missing_root_is_empty(self):
        manifest = build_manifest(self.root / "missing")
        self.assertEqual(manifest["count"], 0)
        self.assertEqual(manifest["train"], [])
        self.assertEqual(manifest["val"], [])

    def test_build_manifest_named_session(self):
        self.write_session("session-a", [{"sample_id": "a1", "rgb": "rgb/a1.png"}])
        self.write_session("session-b", [{"sample_id": "b1", "rgb": "rgb/b1.png"}])

        manifest = build_manifest(self.root, val_fraction=0.0, session="session-b")

        self.assertEqual(manifest["count"], 1)
        self.assertEqual(manifest["sessions"], ["session-b"])
        self.assertEqual(manifest["train"][0]["sample_id"], "b1")


if __name__ == "__main__":
    unittest.main()
