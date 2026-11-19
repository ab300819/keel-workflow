import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

from helpers import CLEAN_ENV, git, make_project, run_keel
from keellib import store
from keellib.store import KeelError, Project

META = "docs/devdocs/state/meta.json"


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name

    def init_project(self, **kw: bool) -> str:
        root = make_project(self.tmp, **kw)
        self.assertEqual(run_keel(root, "init")[0], 0)
        return root

    def violations(self, root: str) -> "list[str]":
        return store.integrity_violations(Project.find(root))

    def test_init_creates_state(self) -> None:
        root = self.init_project()
        self.assertTrue(os.path.isfile(os.path.join(root, META)))
        self.assertTrue(os.path.isdir(os.path.join(root, "docs/devdocs/state/tasks")))
        self.assertTrue(os.path.isdir(os.path.join(root, "docs/devdocs/state/backlog")))
        with open(os.path.join(root, ".keel/manifest.json"), encoding="utf-8") as f:
            self.assertIn(META, json.load(f))

    def test_write_atomic_outside_state_refused(self) -> None:
        p = Project.find(self.init_project())
        with p.lock():
            for rel in ("../escape.json", "docs/devdocs/02-design.md"):
                with self.assertRaises(store.KeelError) as cm:
                    store.write_atomic(p, rel, b"x")
                self.assertEqual(cm.exception.code, 3)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(p.root), "escape.json")))

    def test_tool_write_is_intact(self) -> None:
        self.assertEqual(self.violations(self.init_project()), [])

    def test_head_content_is_intact(self) -> None:
        root = self.init_project()
        git(root, "add", "-A", "-f")
        git(root, "commit", "-qm", "state")
        os.remove(os.path.join(root, ".keel/manifest.json"))
        self.assertEqual(self.violations(root), [])

    def test_hand_edit_detected(self) -> None:
        root = self.init_project()
        with open(os.path.join(root, META), "a", encoding="utf-8") as f:
            f.write("\n")
        self.assertEqual(self.violations(root), [META])
        code, _, err = run_keel(root, "init")
        self.assertEqual(code, 3)
        self.assertIn("state accept", err)

    def test_hand_added_file_detected(self) -> None:
        root = self.init_project()
        p = os.path.join(root, "docs/devdocs/state/tasks/T-1.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write("{}\n")
        self.assertEqual(self.violations(root), ["docs/devdocs/state/tasks/T-1.json"])

    def test_deleted_file_detected(self) -> None:
        root = self.init_project()
        os.remove(os.path.join(root, META))
        self.assertEqual(self.violations(root), [META])

    def test_merge_conflict_message(self) -> None:
        root = self.init_project()
        with open(os.path.join(root, META), "w", encoding="utf-8") as f:
            f.write("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> b\n")
        code, _, err = run_keel(root, "init")
        self.assertEqual(code, 3)
        self.assertIn("合并冲突", err)
        self.assertNotIn("Traceback", err)

    def test_no_git_uses_manifest_only(self) -> None:
        root = self.init_project(git_repo=False)
        self.assertEqual(self.violations(root), [])
        with open(os.path.join(root, META), "w", encoding="utf-8") as f:
            f.write("{}\n")
        self.assertEqual(self.violations(root), [META])

    def test_lock_timeout(self) -> None:
        root = self.init_project()
        code = ("import sys, time; sys.path.insert(0, sys.argv[1])\n"
                "from keellib.store import Project\n"
                "with Project.find(sys.argv[2]).lock():\n"
                "    print('held', flush=True); time.sleep(5)\n")
        scripts = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = subprocess.Popen([sys.executable, "-c", code, scripts, root],
                             stdout=subprocess.PIPE, text=True, env=CLEAN_ENV)
        assert p.stdout is not None
        self.addCleanup(p.stdout.close)
        self.addCleanup(p.wait)
        self.addCleanup(p.kill)
        self.assertEqual(p.stdout.readline().strip(), "held")
        t0 = time.time()
        with self.assertRaises(KeelError) as cm:
            with Project.find(root).lock(timeout=0.2):
                pass
        self.assertEqual(cm.exception.code, 3)
        self.assertLess(time.time() - t0, 2)

    def test_unmigrated_refuses_write(self) -> None:
        root = make_project(self.tmp)
        with open(os.path.join(root, "docs/devdocs/04-dev-tasks.md"), "w", encoding="utf-8") as f:
            f.write("---\nspec_version: tasks.v2\n---\n# 任务\n")
        code, _, err = run_keel(root, "init")
        self.assertEqual(code, 3)
        self.assertIn("/pipeline realign", err)
        self.assertFalse(os.path.exists(os.path.join(root, "docs/devdocs/state")))

    def test_internal_error_exits_3(self) -> None:
        import contextlib
        import io
        from unittest import mock

        import keel
        err = io.StringIO()
        with mock.patch.object(Project, "find", side_effect=RuntimeError("boom")), \
                contextlib.redirect_stderr(err):
            code = keel.main(["init"])
        self.assertEqual(code, 3)
        self.assertEqual(err.getvalue().strip(), "keel 内部错误：boom")

    def test_symlinked_lock_not_truncated(self) -> None:
        root = self.init_project()
        victim = os.path.join(self.tmp + "-victim")
        with open(victim, "w") as f:
            f.write("keep")
        self.addCleanup(os.remove, victim)
        lock = os.path.join(root, ".keel/lock")
        os.remove(lock)
        os.symlink(victim, lock)
        self.assertEqual(run_keel(root, "init")[0], 3)
        with open(victim) as f:
            self.assertEqual(f.read(), "keep")

    def test_symlinked_state_dir_refused(self) -> None:
        root = self.init_project()
        state = os.path.join(root, "docs/devdocs/state")
        os.rename(state, state + "-real")
        os.symlink(state + "-real", state)
        code, _, err = run_keel(root, "init")
        self.assertEqual(code, 3)
        self.assertIn("符号链接", err)

    def test_cleanup_tmp(self) -> None:
        root = self.init_project()
        tmpf = os.path.join(root, "docs/devdocs/state/.meta.json.keel-tmp")
        open(tmpf, "w").close()
        store.cleanup_tmp(Project.find(root))
        self.assertFalse(os.path.exists(tmpf))


if __name__ == "__main__":
    unittest.main()
