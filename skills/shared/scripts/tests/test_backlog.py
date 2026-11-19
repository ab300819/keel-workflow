import json
import os
import tempfile
import unittest

from helpers import make_project, run_keel
from keellib import backlog


class BacklogTest(unittest.TestCase):
    def setUp(self) -> None:
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = make_project(self._t.name)
        self.assertEqual(run_keel(self.root, "init")[0], 0)

    def park(self, sid: str, *extra: str) -> "tuple[int, str, str]":
        return run_keel(self.root, "backlog", "park", sid, "--note", "n", "--by", "verify", *extra)

    def test_park_numbers_increment_and_file_name(self) -> None:
        self.assertEqual(self.park("F-01")[1].strip(), "F-01#1")
        self.assertEqual(self.park("F-01", "--append")[1].strip(), "F-01#2")
        self.assertTrue(os.path.isfile(os.path.join(self.root, backlog.BACKLOG_REL, "F-01-2.json")))
        e = json.loads(run_keel(self.root, "backlog", "get", "F-01#1")[1])
        self.assertIsNone(e["detail"])

    def test_bad_prefix_rejected(self) -> None:
        self.assertEqual(self.park("B-001")[0], 2)

    def test_duplicate_needs_append_except_milestone(self) -> None:
        self.park("F-01")
        rc, _, err = self.park("F-01")
        self.assertEqual(rc, 1)
        self.assertIn("--append", err)
        self.park("M-003")
        self.assertEqual(self.park("M-003")[1].strip(), "M-003#2")

    def test_transitions_only_from_parked(self) -> None:
        self.park("F-01")
        self.assertEqual(run_keel(self.root, "backlog", "close", "F-01#1", "--reason", "r")[0], 0)
        rc, _, err = run_keel(self.root, "backlog", "reactivate", "F-01#1", "--target-flow", "feature", "--target-id", "F-02")
        self.assertEqual(rc, 1)
        self.assertIn("只能从 parked 迁出", err)
        self.assertEqual(run_keel(self.root, "backlog", "note", "F-01#1", "--note", "x")[0], 1)

    def test_reactivate_supersede_missing(self) -> None:
        self.park("F-01")
        self.park("F-02")
        self.assertEqual(run_keel(self.root, "backlog", "reactivate", "F-01#1", "--target-flow", "f", "--target-id", "T-1")[0], 0)
        self.assertEqual(run_keel(self.root, "backlog", "supersede", "F-02#1", "--by-id", "F-03")[0], 0)
        self.assertEqual(json.loads(run_keel(self.root, "backlog", "get", "F-02#1")[1])["status"], "superseded")
        rc, _, err = run_keel(self.root, "backlog", "get", "F-01#9")
        self.assertEqual((rc, err.strip()), (1, "backlog 条目 F-01#9 不存在"))

    def test_list_status_filter(self) -> None:
        self.park("F-01")
        self.park("F-02")
        run_keel(self.root, "backlog", "close", "F-02#1", "--reason", "r")
        out = run_keel(self.root, "backlog", "list", "--status", "parked")[1].splitlines()
        self.assertEqual(out[0], "F-01#1 · parked · n")
        self.assertEqual(len(out), 2)
        self.assertTrue(out[1].startswith("# 扫描 2 个文件，无法识别 0 个"))

    def test_note_cap(self) -> None:
        self.park("F-01")
        self.assertEqual(run_keel(self.root, "backlog", "note", "F-01#1", "--note", "字" * 201)[0], 1)
        self.assertEqual(run_keel(self.root, "backlog", "note", "F-01#1", "--note", "字" * 200)[0], 0)

    def test_traversal_anchor_rejected(self) -> None:
        self.park("F-01")
        rc = run_keel(self.root, "backlog", "close", "../F-01#1", "--reason", "r")[0]
        self.assertEqual(rc, 2)
        self.assertEqual(run_keel(self.root, "backlog", "get", "F-01#1\n")[0], 2)

    def test_mismatched_filename_unreadable(self) -> None:
        self.park("F-01")
        d = os.path.join(self.root, backlog.BACKLOG_REL)
        os.rename(os.path.join(d, "F-01-1.json"), os.path.join(d, "F-09-1.json"))
        out = run_keel(self.root, "backlog", "list")[1]
        self.assertIn("无法识别 1 个", out)


if __name__ == "__main__":
    unittest.main()
