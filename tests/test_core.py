from copy import deepcopy
from pathlib import Path
import unittest

from index_lab.core import replay_index


class IndexTests(unittest.TestCase):
    def test_duplicate_and_stale_updates_preserve_latest_payload_and_input(self):
        data = {"events": [
            {"op": "upsert", "id": "a", "version": 5, "document": {"title": "Current", "tags": ["one"]}},
            {"op": "upsert", "id": "a", "version": 5, "document": {"title": "Duplicate"}},
            {"op": "upsert", "id": "a", "version": 2, "document": {"title": "Old"}}]}
        original = deepcopy(data)
        output = replay_index(data)
        self.assertEqual([row["outcome"] for row in output["results"]], ["indexed", "duplicate", "stale"])
        self.assertEqual(output["documents"], [{"id": "a", "version": 5, "document": {"title": "Current", "tags": ["one"]}}])
        self.assertEqual(data, original)
        output["documents"][0]["document"]["tags"].append("two")
        self.assertEqual(data, original)

    def test_tombstones_block_late_updates_and_allow_higher_versions(self):
        output = replay_index({"events": [
            {"op": "delete", "id": "a", "version": 3},
            {"op": "upsert", "id": "a", "version": 2, "document": {"title": "Old"}},
            {"op": "upsert", "id": "a", "version": 4, "document": {"title": "New"}}]})
        self.assertEqual([row["outcome"] for row in output["results"]], ["deleted", "stale", "indexed"])
        self.assertEqual(output["versions"], [{"id": "a", "version": 4, "deleted": False}])

    def test_document_and_version_order_is_deterministic(self):
        output = replay_index({"events": [
            {"op": "upsert", "id": "b", "version": 1, "document": {}},
            {"op": "delete", "id": "c", "version": 2},
            {"op": "upsert", "id": "a", "version": 1, "document": {}}]})
        self.assertEqual([row["id"] for row in output["documents"]], ["a", "b"])
        self.assertEqual([row["id"] for row in output["versions"]], ["a", "b", "c"])

    def test_invalid_versions_fields_and_ids(self):
        event = {"op": "upsert", "id": "a", "version": 1, "document": {}}
        for bad in ({**event, "version": True}, {**event, "version": 0}, {**event, "document": []},
                    {**event, "id": "a b"}, {"op": "delete", "id": "a", "version": 1, "document": {}}):
            with self.subTest(event=bad), self.assertRaises(ValueError):
                replay_index({"events": [bad]})

    def test_empty_input(self):
        self.assertEqual(replay_index({"events": []}), {"results": [], "documents": [], "versions": []})

    def test_complete_fixture_corpus(self):
        from index_lab.fixture_check import check
        self.assertGreaterEqual(check(Path(__file__).resolve().parents[1] / "fixtures/cases.jsonl", replay_index), 350)


if __name__ == "__main__":
    unittest.main()
