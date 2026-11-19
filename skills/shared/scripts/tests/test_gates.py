import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from helpers import CLEAN_ENV, KEEL, git, make_project, run_keel
import keel  # noqa: E402  须在 helpers 把 scripts 加进 sys.path 之后
from keellib import gates, store

TASKS = "docs/devdocs/04-dev-tasks.md"


class GatesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.root = make_project(self._t.name)
        self.p = store.Project(self.root)

    def write(self, rel: str, text: str) -> None:
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "c")

    def log(self) -> list:
        with open(os.path.join(self.root, ".keel", "gate-log.jsonl"), encoding="utf-8") as f:
            return [json.loads(x) for x in f]

    # K3
    def test_k3_unchanged_long_line_ok_new_long_line_hit(self) -> None:
        old = "旧" * 600
        self.write(TASKS, old + "\n短\n")
        self.commit()
        self.assertEqual(gates.check_k3(self.p, TASKS, old + "\n改\n"), [])
        hit = gates.check_k3(self.p, TASKS, old + "\n" + "新" * 501 + "\n")
        self.assertEqual([(f.gate, f.line) for f in hit], [("K3", 2)])
        self.assertEqual(gates.check_k3(self.p, TASKS, old + "\n" + "新" * 500 + "\n"), [])
        self.assertEqual(len(gates.check_k3(self.p, TASKS, old + "x\n")), 1)

    def test_k3_not_carrier_and_no_head(self) -> None:
        self.assertFalse(gates.is_carrier("docs/devdocs/audit/T-1/x.md"))
        self.assertTrue(gates.is_carrier(TASKS))
        self.assertTrue(gates.is_carrier(".claude/rules/devdocs-state.md"))
        self.assertEqual(len(gates.check_k3(self.p, TASKS, "新" * 501)), 1)  # 无 HEAD 版本

    def test_k3_repo_without_commit(self) -> None:
        with tempfile.TemporaryDirectory() as t:
            p = store.Project(make_project(t, commit=False))
            self.assertEqual(len(gates.check_k3(p, TASKS, "新" * 501)), 1)

    # K4
    def test_k4(self) -> None:
        self.write(TASKS, "a" * (120 * 1024))
        self.commit()
        k = 1024
        self.assertEqual(gates.check_k4(self.p, TASKS, 119 * k), [])
        self.assertEqual(len(gates.check_k4(self.p, TASKS, 121 * k)), 1)
        self.write("docs/devdocs/00-context.md", "a" * (90 * k))
        self.commit()
        self.assertEqual(len(gates.check_k4(self.p, "docs/devdocs/00-context.md", 97 * k)), 1)
        self.assertEqual(gates.check_k4(self.p, "docs/devdocs/backlog.md", 97 * k)[0].gate, "K4")

    # 档位与 CLI
    def test_gate_set_and_levels(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "gate", "set", "K5", "off", "--reason", "x")[0], 2)
        self.assertEqual(run_keel(self.root, "gate", "set", "K3", "bogus", "--reason", "x")[0], 2)
        self.assertEqual(run_keel(self.root, "gate", "set", "K3", "warn", "--reason", "x")[0], 0)
        self.assertEqual(gates.level(self.p, "K3"), "warn")
        self.assertEqual(gates.level(self.p, "K1"), "block")
        self.write(TASKS, "新" * 501 + "\n")
        rc, _, err = run_keel(self.root, "check", "--paths", TASKS)
        self.assertEqual(rc, 0)
        self.assertIn("K3", err)
        self.assertEqual([e["result"] for e in self.log()], ["gate-set", "warn"])
        self.assertEqual(self.log()[1]["client"], "cli")

    def test_check_blocks_by_default_and_off_skips(self) -> None:
        self.write(TASKS, "新" * 501 + "\n")
        rc, _, err = run_keel(self.root, "check")  # 未迁移项目也跑 K3
        self.assertEqual(rc, 1)
        self.assertIn("audit/T-xxx", err)
        self.assertEqual(self.log()[0]["result"], "block")
        blocks, warns = gates.apply_levels(self.p, [], "cli", "check")
        self.assertEqual((blocks, warns), ([], []))

    def test_check_staged_state_file(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")[0], 0)
        rel = "docs/devdocs/state/tasks/T-1.json"
        self.write(rel, '{"id": "T-1", "hand": true}\n')
        git(self.root, "add", rel)
        rc, _, err = run_keel(self.root, "check", "--staged")
        self.assertEqual(rc, 1)
        self.assertIn("K1", err)
        self.assertIn(rel, err)

    # state accept
    def test_accept_needs_tty(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        p = subprocess.run([sys.executable, KEEL, "--root", self.root, "state", "accept"], capture_output=True,
                           text=True, env=CLEAN_ENV, start_new_session=True, stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 3)
        self.assertIn("! .keel/bin/keel state accept", p.stderr)

    def test_accept_success_and_refusal(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")[0], 0)
        rel = "docs/devdocs/state/tasks/T-1.json"
        self.write(rel, '{"id": "T-1", "hand": true}\n')
        self.assertTrue(store.integrity_violations(self.p))
        with mock.patch("keellib.gates.read_tty", return_value="no"):
            self.assertEqual(keel.main(["--root", self.root, "state", "accept"]), 1)
        self.assertTrue(store.integrity_violations(self.p))
        with mock.patch("keellib.gates.read_tty", return_value="accept") as m:
            self.assertEqual(keel.main(["--root", self.root, "state", "accept"]), 0)
        self.assertIn(rel, m.call_args[0][0])
        self.assertEqual(store.integrity_violations(self.p), [])
        self.assertEqual(self.log()[-1]["result"], "accept")

    # report
    def test_report(self) -> None:
        for g, path in (("K3", "a.md"), ("K3", "b.md"), ("K3", "a.md"), ("K1", "s.json")):
            gates.log_hit(self.p, g, "block", "block", "cli", "check", path, "d")
        rc, out, _ = run_keel(self.root, "gate", "report")
        self.assertEqual(rc, 0)
        self.assertRegex(out, r"K3\s+3")
        self.assertRegex(out, r"K1\s+1")
        self.assertIn("每卡派生数", out)
        rc, out, _ = run_keel(self.root, "gate", "report", "--since", "2999-01-01")
        self.assertNotIn("K3", out.split("每卡派生数")[0])


if __name__ == "__main__":
    unittest.main()
