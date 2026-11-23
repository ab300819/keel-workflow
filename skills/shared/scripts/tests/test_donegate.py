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

    def test_mixed_short_long_squash_rejected(self) -> None:
        self.add()
        s = self.make_commit({"test_a.py": "assert f() == 1\n", "a.py": "def f():\n    return 1\n"})
        self.reg(s[:7], test=True)
        self.reg(s)
        self.record()
        self.assert_rejected(PENDING, "之前没有测试提交")

    def _freeze_case(self, name: str) -> None:
        self.add()
        helpers.git(self.root, "config", "core.quotepath", "true")  # 默认值；本机全局配置可能关了它
        t = self.make_commit({name: "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n", name: "assert f() == 2\n"})
        self.reg(t, test=True)
        self.reg(c)
        self.record()
        self.assert_rejected(PENDING, "之后改了测试")

    def test_freeze_with_space_in_name(self) -> None:
        self._freeze_case("test_a x.py")  # 按空白切分会得到 x.py，避开 a.py

    def test_freeze_with_non_ascii_name(self) -> None:
        self._freeze_case("测试_test.py")

    def test_later_test_commit_may_edit_earlier_test(self) -> None:
        self.add()
        t1 = self.make_commit({"test_a.py": "assert f() == 1\n"})
        t2 = self.make_commit({"test_a.py": "assert f() == 1\nassert f() > 0\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        self.reg(t1, test=True)
        self.reg(t2, test=True)
        self.reg(c)
        self.record()
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *PENDING)
        self.assertEqual(rc, 0, err)

    def _run(self, plan: "list[tuple[str, bool]]") -> "tuple[int, str]":
        self.record()
        for sha, test in plan:
            self.reg(sha, test=test)
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *PENDING)
        return rc, err

    def test_skeleton_in_test_commit_not_frozen(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n", "a.py": "def f():\n    raise NotImplementedError\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        rc, err = self._run([(t, True), (c, False)])
        self.assertEqual(rc, 0, err)

    def test_test_file_beside_skeleton_still_frozen(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n", "a.py": "def f():\n    raise NotImplementedError\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n", "test_a.py": "assert f() == 2\n"})
        rc, err = self._run([(t, True), (c, False)])
        self.assertEqual(rc, 1)
        self.assertIn("之后改了测试", err)

    def test_test_commit_without_test_files_rejected(self) -> None:
        self.add()
        t = self.make_commit({"a.py": "def f():\n    raise NotImplementedError\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        rc, err = self._run([(t, True), (c, False)])
        self.assertEqual(rc, 1)
        self.assertIn(f"测试提交 {t} 里没有识别出测试文件（按路径规则）", err)

    def test_test_path_patterns(self) -> None:
        from keellib import donegate
        for p in ("tests/a.py", "src/__tests__/a.js", "spec/a.rb", "a/test/b.go", "test_a.py", "a_test.go",
                  "a.test.ts", "a.spec.ts", "FooTest.java", "FooTests.cs", "a_spec.rb"):
            self.assertTrue(donegate.is_test_path(p), p)
        for p in ("a.py", "src/testing.py", "latest.py", "contest/a.py"):
            self.assertFalse(donegate.is_test_path(p), p)

    def _weaken_plan(self) -> "list[tuple[str, bool]]":
        self.add()
        t1 = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c1 = self.make_commit({"a.py": "def f():\n    return 2\n"})
        t2 = self.make_commit({"test_a.py": "assert f() == 2\n"})
        c2 = self.make_commit({"b.py": "x = 1\n"})
        return [(t1, True), (c1, False), (t2, True), (c2, False)]

    def test_test_edited_after_code_commit_rejected(self) -> None:
        rc, err = self._run(self._weaken_plan())
        self.assertEqual(rc, 1)
        self.assertIn("之后改了测试", err)

    def test_test_edited_after_code_commit_rejected_out_of_order(self) -> None:
        t1, c1, t2, c2 = self._weaken_plan()
        rc, err = self._run([t2, c2, c1, t1])
        self.assertEqual(rc, 1)
        self.assertIn("之后改了测试", err)

    def test_later_test_commit_edit_out_of_order_registration(self) -> None:
        self.add()
        t1 = self.make_commit({"test_a.py": "assert f() == 1\n"})
        t2 = self.make_commit({"test_a.py": "assert f() == 1\nassert f() > 0\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        rc, err = self._run([(c, False), (t2, True), (t1, True)])
        self.assertEqual(rc, 0, err)

    def test_root_commit_test_still_frozen(self) -> None:
        self.add()
        os.makedirs(os.path.join(self.root, "svc"))
        helpers.git(os.path.join(self.root, "svc"), "init", "-q")
        t = self.make_commit({"test_a.py": "assert f() == 1\n"}, repo="svc")
        c = self.make_commit({"a.py": "def f():\n    return 1\n", "test_a.py": "assert f() == 2\n"}, repo="svc")
        self.record()
        self.reg(t, test=True, repo="svc")
        self.reg(c, repo="svc")
        self.assert_rejected(PENDING, "之后改了测试")

    def test_merge_base_failure_is_git_error(self) -> None:
        from keellib import donegate
        from keellib.store import KeelError
        with self.assertRaises(KeelError) as cm:
            donegate._is_ancestor(self.root, "HEAD:docs", "HEAD")  # 树对象，merge-base 退出码 128
        self.assertIn("git merge-base", str(cm.exception))

    def test_record_outside_project_rejected(self) -> None:
        self.add()
        t = self.make_commit({"test_a.py": "assert f() == 1\n"})
        c = self.make_commit({"a.py": "def f():\n    return 1\n"})
        self.reg(t, test=True)
        self.reg(c)
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        rel = os.path.relpath(os.path.realpath(other.name), self.root)  # ../../tmpXXX，真实存在
        self.assertEqual(run_keel(self.root, "task", "set", "T-1", "--record", rel)[0], 0)
        self.assert_rejected(PENDING, "注错记录")

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
        self.assert_rejected(PENDING, "linked 代码根在项目外时，完成门暂不支持登记测试提交")

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

    def test_repo_without_test_commits_skipped(self) -> None:
        self.add()
        os.makedirs(os.path.join(self.root, "svc"))
        helpers.git(os.path.join(self.root, "svc"), "init", "-q")
        t = self.make_commit({"test_a.py": "assert f() == 1\n"}, repo="svc")
        c = self.make_commit({"a.py": "def f():\n    return 1\n"}, repo="svc")
        cfg = self.make_commit({"cfg.yml": "a: 1\n"})
        self.reg(t, test=True, repo="svc")
        self.reg(c, repo="svc")
        self.reg(cfg, repo="app")
        self.record()
        rc, _, err = run_keel(self.root, "task", "set", "T-1", *PENDING)
        self.assertEqual(rc, 0, err)

    def test_repo_outside_project_not_used(self) -> None:
        self.add()
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        out = os.path.realpath(other.name)
        helpers.git(out, "init", "-q")
        rel = os.path.relpath(out, self.root)  # ../../tmpXXX 形式
        t = self.make_commit({"test_a.py": "assert f() == 1\n"}, repo=rel)
        self.reg(t, test=True, repo=rel)
        self.record()
        self.assert_rejected(PENDING, "解析不到")

    def test_move_check_ignores_external_diff(self) -> None:
        self.add("move")
        self.make_commit({"a.py": "def f(x):\n    y = g(x)\n    if y > 1:\n        h(y)\n"})
        c = self.make_commit({"a.py": None, "b.py": "def f(x):\n    y = g(x)\n    if y > 2:\n        h(y)\n"})
        helpers.git(self.root, "config", "diff.external", "false")
        self.reg(c)
        self.assert_rejected(("--status", "已完成"), "改 --profile guarded")

    def test_move_with_logic_glue_rejected(self) -> None:
        self.add("move")
        self.make_commit({"a.py": "def f(x):\n    y = g(x)\n    if y > 1:\n        h(y)\n"})
        c = self.make_commit({"a.py": None, "b.py": "def f(x):\n    y = g(x)\n    if y > 2:\n        h(y)\n"})
        self.reg(c)
        self.assert_rejected(("--status", "已完成"), "改 --profile guarded")
        rc, _, err = run_keel(self.root, "task", "set", "T-1", "--profile", "guarded", *PENDING)
        self.assertEqual(rc, 0, err)

    def test_move_comparison_flip_rejected(self) -> None:
        self.add("move")
        self.make_commit({"a.py": "def f(a, b):\n    ok = a < b\n    use(ok)\n"})
        c = self.make_commit({"a.py": None, "b.py": "def f(a, b):\n    ok = a > b\n    use(ok)\n"})
        self.reg(c)
        self.assert_rejected(("--status", "已完成"), "b.py:2 + ok = a > b")

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
