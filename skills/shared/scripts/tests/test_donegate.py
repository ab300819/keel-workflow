import os
import subprocess
import tempfile
import unittest

import helpers
from helpers import make_project, run_keel
from keellib import tasks

PENDING = ("--status", "review_pending", "--batch", "b", "--due", "2026-12-01", "--pending-reason", "deferred-fast")


class DoneGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = make_project(self._t.name)
        self.assertEqual(run_keel(self.root, "init")[0], 0)

    def add(self, profile: str = "fast") -> None:
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks",
                                  "--profile", profile)[0], 0)

    def make_commit(self, files: "dict[str, str | None]", repo: str = "") -> str:
        d = os.path.join(self.root, repo)
        for name, text in files.items():
            p = os.path.join(d, name)
            if text is None:
                os.remove(p)
            else:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(text)
        helpers.git(d, "add", "--", *files)
        helpers.git(d, "commit", "-qm", "c")
        return subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True,
                              env=helpers.CLEAN_ENV, check=True).stdout.strip()

    def reg(self, sha: str, test: bool = False, repo: str = "app") -> None:
        extra = ("--kind", "test") if test else ()
        self.assertEqual(run_keel(self.root, "task", "commit", "T-1", f"{repo}@{sha}", "--note", "n", *extra)[0], 0)

    def record(self) -> None:
        os.makedirs(os.path.join(self.root, "audit", "T-1"))
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--record", "audit/T-1/")[0], 0)

    def raw(self) -> bytes:
        with open(os.path.join(self.root, tasks.TASKS_REL, "T-1.json"), "rb") as f:
            return f.read()

    def assert_rejected(self, args: "tuple[str, ...]", needle: str) -> None:
        before = self.raw()
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *args)
        self.assertEqual(rc, 1, err)
        self.assertIn(needle, err)
        self.assertEqual(self.raw(), before)

    def test_gate_skipped_without_test_commits_or_move(self) -> None:
        self.add()
        self.reg("abcdef1")
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--status", "已完成")[0], 0)

    def test_test_before_code_passes(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.record()
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *PENDING)
        self.assertEqual(rc, 0, err)

    def test_code_without_prior_test_rejected(self) -> None:
        self.add()
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.record()
        self.assert_rejected(PENDING, "之前没有测试提交")

    def test_test_modified_after_freeze_rejected(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n", "test_a.py": "assert f() == 2\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.record()
        self.assert_rejected(PENDING, "之后改了测试")

    def test_squashed_rejected(self) -> None:
        self.add()
        s = self.make_commit({"test_a.py": "assert f() == 1\n", "a.py": "def f():\n    return 1\n"})
        self.reg(s, test=True)
        self.reg(s)
        self.record()
        self.assert_rejected(PENDING, "之前没有测试提交")

    def test_missing_record_rejected(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.assert_rejected(PENDING, "注错记录")

    def test_unresolvable_sha_rejected(self) -> None:
        self.add()
        self.reg("a" * 40, test=True)
        self.record()
        self.assert_rejected(PENDING, "解析不到")

    def test_resolves_sha_in_subrepo_dir(self) -> None:
        self.add()
        os.makedirs(os.path.join(self.root, "svc"))
        helpers.git(os.path.join(self.root, "svc"), "init", "-q")
        t = self.make_commit({"test_a.py": "assert f() == 1\n"}, repo="svc")
        c = self.make_commit({"a.py": "def f():\n    return 1\n"}, repo="svc")
        self.reg(t, test=True, repo="svc")
        self.reg(c, repo="svc")
        self.record()
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *PENDING)
        self.assertEqual(rc, 0, err)

    def test_move_with_logic_glue_rejected(self) -> None:
        self.add("move")
        self.make_commit({"a.py": "def f(x):\n    y = g(x)\n    if y > 1:\n        h(y)\n"})
        c = self.make_commit({"a.py": None, "b.py": "def f(x):\n    y = g(x)\n    if y > 2:\n        h(y)\n"})
        self.reg(c)
        self.assert_rejected(("--status", "已完成"), "改 --profile guarded")
        rc, _, err = run_keel(self.root, "task", "set", "T-1", "--profile", "guarded", *PENDING)
        self.assertEqual(rc, 0, err)

    def test_move_pure_passes(self) -> None:
        self.add("move")
        self.make_commit({"a.py": "def f(x):\n    y = g(x)\n    if y > 1:\n        h(y)\n"})
        c = self.make_commit({"a.py": None, "b.py": "def f(x):\n    y = g(x)\n    if y > 1:\n        h(y)\n"})
        self.reg(c)
        rc, _, err = run_keel(self.root, "task", "set", "T-1", "--status", "已完成")
        self.assertEqual(rc, 0, err)

    def test_gate_only_on_status_change(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.record()
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--status", "已完成")[0], 0)
        os.rmdir(os.path.join(self.root, "audit", "T-1"))
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--title", "y")[0], 0)


if __name__ == "__main__":
    unittest.main()
