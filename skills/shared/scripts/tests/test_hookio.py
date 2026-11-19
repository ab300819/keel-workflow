import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock

from helpers import CLEAN_ENV, SCRIPTS, git, make_project, run_keel
import keel  # noqa: E402  须在 helpers 把 scripts 加进 sys.path 之后
from keellib import hookio

STATE_T1 = "docs/devdocs/state/tasks/T-1.json"
TASKS = "docs/devdocs/04-dev-tasks.md"
PATCH = ("*** Begin Patch\n*** Update File: docs/a.md\n*** Move to: docs/b.md\n@@\n-x\n+y\n"
         "*** Add File: src/c.py\n+z\n*** End Patch\n")


class HookioTest(unittest.TestCase):
    def setUp(self) -> None:
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = make_project(self._t.name)

    def hook(self, event: str, payload: dict) -> "tuple[int, str]":
        rc, out, err = run_keel(self.root, "hook", event, stdin=json.dumps(payload))
        self.assertEqual(err, "")
        return rc, out

    def migrated(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")[0], 0)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "state")

    def write(self, rel: str, text: str) -> None:
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    # edited_paths
    def test_edited_paths_three_shapes(self) -> None:
        r = self.root
        self.assertEqual(hookio.edited_paths({"tool_name": "Edit", "tool_input": {"file_path": r + "/" + STATE_T1}}, r),
                         [STATE_T1])
        self.assertEqual(hookio.edited_paths({"tool_name": "apply_patch", "tool_input": {"command": PATCH}}, r),
                         ["docs/a.md", "docs/b.md", "src/c.py"])
        self.assertEqual(hookio.edited_paths({"tool_name": "patch", "tool_input": {"patchText": PATCH}}, r),
                         ["docs/a.md", "docs/b.md", "src/c.py"])
        self.assertEqual(hookio.edited_paths({"tool_input": {"filePath": "x/../src/a.py"}}, r), ["src/a.py"])
        self.assertEqual(hookio.edited_paths({}, r), [])

    def test_hook_paths_cli(self) -> None:
        rc, out, _ = run_keel(self.root, "hook", "paths", stdin=json.dumps({"tool_input": {"patchText": PATCH}}))
        self.assertEqual((rc, out), (0, "docs/a.md\ndocs/b.md\nsrc/c.py\n"))

    # Pre
    def test_pre_denies_state_and_keel_dir(self) -> None:
        self.migrated()
        rc, out = self.hook("pre", {"tool_name": "Edit", "tool_input": {"file_path": self.root + "/" + STATE_T1}})
        d = json.loads(out)["hookSpecificOutput"]
        self.assertEqual((rc, d["permissionDecision"]), (0, "deny"))
        self.assertIn("K1", d["permissionDecisionReason"])
        rc, out = self.hook("pre", {"tool_name": "Write", "tool_input": {"file_path": ".keel/manifest.json"}})
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.hook("pre", {"tool_name": "Edit", "tool_input": {"file_path": "src/a.py"}}), (0, ""))
        with open(os.path.join(self.root, ".keel", "gate-log.jsonl"), encoding="utf-8") as f:
            self.assertEqual([json.loads(x)["client"] for x in f], ["claude", "claude"])

    def deny(self, payload: dict) -> bool:
        out = self.hook("pre", payload)[1]
        return bool(out) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_pre_path_aliases_denied(self) -> None:
        self.migrated()
        self.assertTrue(self.deny({"tool_name": "Edit", "tool_input": {
            "file_path": self.root + "/docs/devdocs/State/tasks/T-1.json"}}))
        os.symlink(os.path.join(self.root, STATE_T1), os.path.join(self.root, "docs", "link.json"))
        self.assertTrue(self.deny({"tool_name": "Write", "tool_input": {"file_path": "docs/link.json"}}))
        self.assertTrue(self.deny({"tool_name": "NotebookEdit", "tool_input": {
            "notebook_path": self.root + "/docs/devdocs/state/x.ipynb"}}))
        self.assertTrue(self.deny({"tool_name": "Edit", "tool_input": {"file_path": "docs/devdocs/BACKLOG.md"}}))
        self.assertFalse(self.deny({"tool_name": "Edit", "tool_input": {"file_path": "docs/devdocs/statex/a.md"}}))

    def test_pre_human_rule_anchored_to_command(self) -> None:
        for cmd in ('grep -rn "keel state accept" docs/', 'git commit -m "说明 keel state accept 的用法"',
                    "cat .keel/bin/keel | grep 'gate set K3 off'"):
            self.assertFalse(self.deny({"tool_name": "Bash", "tool_input": {"command": cmd}}), cmd)
        for cmd in (".keel/bin/keel state accept", "python3 x/keel.py gate set K1 off --reason r",
                    "cd a && .keel/bin/keel state accept", "X=1 bash .keel/bin/keel state accept",
                    "echo $(keel state accept)", "ls\nkeel gate set K2 warn --reason r"):
            self.assertTrue(self.deny({"tool_name": "Bash", "tool_input": {"command": cmd}}), cmd)

    def test_pre_unmigrated_allows_backlog(self) -> None:
        self.assertEqual(self.hook("pre", {"tool_name": "apply_patch", "tool_input": {
            "command": "*** Update File: docs/devdocs/backlog.md\n"}}), (0, ""))

    def test_pre_bash_human_only_commands(self) -> None:
        for cmd in (".keel/bin/keel state accept", "python3 x/keel.py --root . gate set K3 off --reason y",
                    "cd a && keel gate set K1 warn --reason z"):
            rc, out = self.hook("pre", {"tool_name": "Bash", "tool_input": {"command": cmd}})
            d = json.loads(out)["hookSpecificOutput"]
            self.assertEqual(d["permissionDecision"], "deny", cmd)
            self.assertIn("! .keel/bin/keel", d["permissionDecisionReason"])
        for cmd in (".keel/bin/keel gate set K3 block --reason y", ".keel/bin/keel task list", "echo state accept"):
            self.assertEqual(self.hook("pre", {"tool_name": "shell", "tool_input": {"command": ["bash", "-lc", cmd]}}),
                             (0, ""), cmd)
        with open(os.path.join(self.root, ".keel", "gate-log.jsonl"), encoding="utf-8") as f:
            self.assertEqual({json.loads(x)["gate"] for x in f}, {"human"})

    def test_pre_bash_not_path_denied(self) -> None:
        self.migrated()
        self.assertEqual(self.hook("pre", {"tool_name": "Bash", "tool_input": {"command": "echo x > " + STATE_T1}}),
                         (0, ""))

    def test_hook_fails_open(self) -> None:
        rc, out, err = run_keel(self.root, "hook", "pre", stdin="not json")
        self.assertEqual((rc, out, err), (0, "", ""))
        with mock.patch("keellib.hookio.pre", side_effect=RuntimeError("boom")), \
                mock.patch("sys.stdin") as stdin:
            stdin.read.return_value = "{}"
            self.assertEqual(keel.main(["--root", self.root, "hook", "pre"]), 0)
        with open(os.path.join(self.root, ".keel", "gate-log.jsonl"), encoding="utf-8") as f:
            self.assertIn("hook-error", f.read())

    # Post
    def test_post_blocks_hand_edited_state(self) -> None:
        self.migrated()
        self.write(STATE_T1, '{"id": "T-1", "hand": true}\n')
        rc, out = self.hook("post", {"tool_name": "Bash", "tool_input": {"command": "x"}})
        d = json.loads(out)
        self.assertEqual((rc, d["decision"]), (0, "block"))
        self.assertIn(STATE_T1, d["reason"])

    def test_post_k3_warn_gives_context(self) -> None:
        self.migrated()
        with mock.patch("keellib.gates.read_tty", return_value="accept"):
            self.assertEqual(keel.main(["--root", self.root, "gate", "set", "K3", "warn", "--reason", "x"]), 0)
        with open(os.path.join(self.root, TASKS), "a", encoding="utf-8") as f:
            f.write("新" * 501 + "\n")
        rc, out = self.hook("post", {"tool_name": "Edit", "tool_input": {"file_path": TASKS}})
        d = json.loads(out)
        self.assertNotIn("decision", d)
        self.assertIn("K3", d["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook("post", {"tool_name": "Edit", "tool_input": {"file_path": "src/a.py"}})[0], 0)

    def test_post_clean_is_silent(self) -> None:
        self.migrated()
        self.assertEqual(self.hook("post", {"tool_name": "Edit", "tool_input": {"file_path": "src/a.py"}}), (0, ""))

    # install
    def test_install_shim_in_worktree(self) -> None:
        git(self.root, "worktree", "add", "-q", "-b", "wt", os.path.join(self.root, "..", "wt"))
        wt = os.path.realpath(os.path.join(self.root, "..", "wt"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", wt]))
        self.assertTrue(os.path.isfile(os.path.join(wt, ".git")))
        for _ in range(2):
            rc, out, err = run_keel(wt, "install-shim", "--plugin-root", "/opt/keel plug")
            self.assertEqual((rc, out, err), (0, "", ""))
        with open(os.path.join(wt, ".keel", "bin", "keel"), encoding="utf-8") as f:
            self.assertIn("'/opt/keel plug/skills/shared/scripts/keel.py'", f.read())
        self.assertTrue(os.access(os.path.join(wt, ".keel", "bin", "keel"), os.X_OK))
        ex = subprocess.run(["git", "-C", wt, "rev-parse", "--git-path", "info/exclude"], capture_output=True,
                            text=True, env=CLEAN_ENV).stdout.strip()
        with open(os.path.join(wt, ex), encoding="utf-8") as f:
            self.assertEqual(f.read().splitlines().count(".keel/"), 1)

    def test_install_shim_unmigrated_hint(self) -> None:
        self.write("docs/devdocs/04-dev-tasks.md", "---\nspec_version: tasks.v2\n---\n")
        rc, out, _ = run_keel(self.root, "install-shim", "--plugin-root", "/p")
        self.assertEqual(rc, 0)
        self.assertIn("/pipeline realign", json.loads(out)["hookSpecificOutput"]["additionalContext"])

    def test_git_hook_install_chains_once(self) -> None:
        hooks = os.path.join(self.root, ".git", "hooks")
        os.makedirs(hooks, exist_ok=True)
        with open(os.path.join(hooks, "pre-commit"), "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho old-hook\n")
        os.chmod(os.path.join(hooks, "pre-commit"), 0o755)
        rc, out, _ = run_keel(self.root, "git-hook", "install")
        self.assertEqual(rc, 0)
        self.assertIn("pre-commit.keel-chained", out)
        rc, out, _ = run_keel(self.root, "git-hook", "install")
        self.assertEqual(rc, 0)
        with open(os.path.join(hooks, "pre-commit.keel-chained"), encoding="utf-8") as f:
            self.assertIn("old-hook", f.read())
        self.assertEqual(sorted(n for n in os.listdir(hooks) if n.startswith("pre-commit") and not n.endswith(".sample")),
                         ["pre-commit", "pre-commit.keel-chained"])
        # 垫片不存在：警告放行并执行旧 hook
        p = subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                            "-q", "--allow-empty", "-m", "x"], capture_output=True, text=True, env=CLEAN_ENV)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("old-hook", p.stdout + p.stderr)

    def commit_empty(self) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                               "-q", "--allow-empty", "-m", "x"], capture_output=True, text=True, env=CLEAN_ENV)

    def test_git_hook_keel_unavailable_allows_commit(self) -> None:
        self.assertEqual(run_keel(self.root, "install-shim", "--plugin-root", "/nonexistent/keel")[0], 0)
        self.assertEqual(run_keel(self.root, "git-hook", "install")[0], 0)
        p = self.commit_empty()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("keel 不可用（退出码 2）", p.stderr)

    def test_git_hook_tracked_hooks_path_warns(self) -> None:
        git(self.root, "config", "core.hooksPath", ".githooks")
        rc, out, _ = run_keel(self.root, "git-hook", "install")
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.root, ".githooks", "pre-commit")))
        self.assertIn("团队", out)

    def test_git_hook_blocks_hand_edited_state(self) -> None:
        self.migrated()
        plugin = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS)))
        self.assertEqual(run_keel(self.root, "install-shim", "--plugin-root", plugin)[0], 0)
        self.assertEqual(run_keel(self.root, "git-hook", "install")[0], 0)
        self.write(STATE_T1, '{"id": "T-1", "hand": true}\n')
        git(self.root, "add", STATE_T1)
        p = subprocess.run(["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit",
                            "-qm", "x"], capture_output=True, text=True, env=CLEAN_ENV)
        self.assertEqual(p.returncode, 1)
        self.assertIn("K1", p.stderr)


if __name__ == "__main__":
    unittest.main()
