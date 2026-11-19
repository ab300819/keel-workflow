import json
import os
import subprocess
import sys
import tempfile
import unittest

from helpers import CLEAN_ENV, KEEL, make_project, run_keel
from keellib import schema, store, tasks


class TaskTest(unittest.TestCase):
    def setUp(self) -> None:
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = make_project(self._t.name)
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.p = store.Project(self.root)

    def seed(self, *nums: int) -> None:
        with self.p.lock():
            for n in nums:
                t = schema.new_task(f"T-{n}", f"任务{n}", "dev-tasks")
                store.write_atomic(self.p, f"{tasks.TASKS_REL}/T-{n}.json", tasks._dump(t))

    def path(self, tid: str) -> str:
        return os.path.join(self.root, tasks.TASKS_REL, tid + ".json")

    def raw(self, tid: str) -> bytes:
        with open(self.path(tid), "rb") as f:
            return f.read()

    def test_add_allocates_next_id(self) -> None:
        self.seed(7, 12)
        rc, out, _ = run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")
        self.assertEqual((rc, out.strip()), (0, "T-13"))

    def test_add_requires_source(self) -> None:
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x")[0], 2)

    def test_set_multiple_fields_atomic(self) -> None:
        self.seed(1)
        rc = run_keel(self.root, "task", "set", "T-1", "--status", "review_pending", "--batch", "b1",
                      "--due", "2026-11-30", "--pending-reason", "deferred-fast")[0]
        self.assertEqual(rc, 0)
        before = self.raw("T-1")
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--due", "")[0], 1)
        self.assertEqual(self.raw("T-1"), before)

    def test_set_review_pending_alone_rejected(self) -> None:
        self.seed(1)
        before = self.raw("T-1")
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--status", "review_pending")[0], 1)
        self.assertEqual(self.raw("T-1"), before)

    def test_concurrent_set_keeps_both(self) -> None:
        self.seed(1)
        cmds = [["--milestone", "M-1"], ["--layer", "core"]]
        ps = [subprocess.Popen([sys.executable, KEEL, "--root", self.root, "task", "set", "T-1", *c],
                               env=CLEAN_ENV, stderr=subprocess.PIPE, text=True) for c in cmds]
        for p in ps:
            self.assertEqual(p.wait(), 0, p.stderr.read() if p.stderr else "")
        t = json.loads(self.raw("T-1"))
        self.assertEqual((t["milestone"], t["layer"]), ("M-1", "core"))

    def test_list_reports_unreadable(self) -> None:
        self.seed(1)
        with open(os.path.join(self.root, tasks.TASKS_REL, "bad.json"), "w") as f:
            f.write("{")
        rc, out, _ = run_keel(self.root, "task", "list")
        self.assertEqual(rc, 0)
        last = out.strip().splitlines()[-1]
        self.assertIn("无法识别 1 个", last)
        self.assertIn("bad.json", last)

    def test_list_fields(self) -> None:
        self.seed(1)
        _, out, _ = run_keel(self.root, "task", "list", "--fields", "id,status")
        self.assertEqual(out.splitlines()[:-1], ["T-1 · 待开发"])

    def test_commit_archive_get(self) -> None:
        self.seed(1)
        self.assertEqual(run_keel(self.root, "task", "commit", "T-1", "repo@abc1234", "--note", "n")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "archive", "T-1")[0], 0)
        t = json.loads(run_keel(self.root, "task", "get", "T-1")[1])
        self.assertEqual((t["status"], t["commits"][0]["ref"]), ("已归档", "repo@abc1234"))
        self.assertEqual(run_keel(self.root, "task", "get", "T-9")[0], 1)

    def test_write_refused_when_tampered(self) -> None:
        self.seed(1)
        with open(self.path("T-1"), "a") as f:
            f.write(" ")
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--layer", "x")[0], 3)


if __name__ == "__main__":
    unittest.main()
