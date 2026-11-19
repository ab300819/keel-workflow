import json
import os
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
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

    def main_accept(self, *args: str, answer: str = "accept") -> int:
        with mock.patch("keellib.gates.read_tty", return_value=answer):
            return keel.main(["--root", self.root, *args])

    def notty(self, *args: str) -> "subprocess.CompletedProcess[str]":
        return subprocess.run([sys.executable, KEEL, "--root", self.root, *args], capture_output=True, text=True,
                              env=CLEAN_ENV, start_new_session=True, stdin=subprocess.DEVNULL)

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
        self.assertEqual(self.main_accept("gate", "set", "K3", "warn", "--reason", "x"), 0)
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
        self.assertIn("K3 2（共命中 3 次）", out)
        self.assertIn("K1 1（共命中 1 次）", out)
        self.assertIn("每卡派生数", out)
        rc, out, _ = run_keel(self.root, "gate", "report", "--since", "2999-01-01")
        self.assertNotIn("K3", out.split("每卡派生数")[0])

    # fix round 1
    def test_read_tty_on_real_pty(self) -> None:
        pid, fd = pty.fork()
        if pid == 0:
            try:
                got = gates.read_tty("确认：")
            except BaseException:
                os._exit(7)
            os._exit(0 if got == "accept" else 5)
        deadline = time.monotonic() + 10
        buf = b""
        sent = False
        status = None
        while status is None and time.monotonic() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                try:
                    buf += os.read(fd, 1024)  # 要持续排空，否则 child 退出会卡在未读输出上
                except OSError:  # EIO：child 已退出（Linux）
                    pass
            if not sent and "确认".encode() in buf:  # 等提示出现再输入，避免输入被 tty 初始化冲掉
                os.write(fd, b"accept\n")
                sent = True
            done, st = os.waitpid(pid, os.WNOHANG)
            status = st if done else None
        os.close(fd)
        if status is None:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            self.fail("read_tty 在 pty 上 10 秒内没有返回")
        self.assertEqual(status, 0)

    def test_forged_gates_json_ignored(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(self.main_accept("gate", "set", "K3", "warn", "--reason", "x"), 0)
        self.write(gates.GATES_REL, json.dumps({"K1": {"level": "off"}}))
        self.assertEqual(gates.level(self.p, "K1"), "block")
        rc, _, err = run_keel(self.root, "check")
        self.assertEqual(rc, 1)
        self.assertIn("K1", err)

    def test_symlinked_log_refused(self) -> None:
        outside = os.path.join(self._t.name + "-out.txt")
        self.addCleanup(lambda: os.path.exists(outside) and os.remove(outside))
        with open(outside, "w") as f:
            f.write("keep\n")
        os.makedirs(os.path.join(self.root, ".keel"))
        os.symlink(outside, os.path.join(self.root, gates.LOG_REL))
        self.write(TASKS, "新" * 501 + "\n")
        self.assertEqual(run_keel(self.root, "check")[0], 3)
        with open(outside) as f:
            self.assertEqual(f.read(), "keep\n")

    def test_lowering_needs_human(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        p = self.notty("gate", "set", "K1", "off", "--reason", "x")
        self.assertEqual(p.returncode, 3)
        self.assertIn("! .keel/bin/keel gate set", p.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.root, gates.GATES_REL)))
        self.assertEqual(self.main_accept("gate", "set", "K1", "off", "--reason", "x", answer="no"), 1)
        self.assertEqual(self.main_accept("gate", "set", "K1", "off", "--reason", "x"), 0)
        self.assertEqual(gates.level(self.p, "K1"), "off")
        self.assertEqual(self.notty("gate", "set", "K1", "warn", "--reason", "x").returncode, 0)  # 抬高不需 tty
        self.assertEqual(gates.level(self.p, "K1"), "warn")
        self.assertEqual(self.notty("gate", "set", "K1", "warn", "--reason", "y").returncode, 0)  # 同档

    def test_accept_state_changed_during_prompt(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")[0], 0)
        rel = "docs/devdocs/state/tasks/T-1.json"
        self.write(rel, '{"id": "T-1", "hand": 1}\n')

        def sneaky(_prompt: str) -> str:
            self.write(rel, '{"id": "T-1", "hand": 2}\n')
            return "accept"
        with mock.patch("keellib.gates.read_tty", side_effect=sneaky):
            self.assertEqual(keel.main(["--root", self.root, "state", "accept"]), 1)
        self.assertTrue(store.integrity_violations(self.p))

    def test_root_subdir(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")[0], 0)
        rel = "docs/devdocs/state/tasks/T-1.json"
        self.write(rel, '{"id": "T-1", "hand": true}\n')
        git(self.root, "add", rel)
        rc, _, err = run_keel(os.path.join(self.root, "docs"), "check", "--staged")
        self.assertEqual(rc, 1)
        self.assertIn("K1", err)

    def test_report_counts_distinct_findings(self) -> None:
        for _ in range(5):
            gates.log_hit(self.p, "K3", "block", "block", "claude", "Bash", "a.md", "同一条")
        rc, out, _ = run_keel(self.root, "gate", "report")
        self.assertEqual(rc, 0)
        self.assertIn("K3 1（共命中 5 次）  a.md", out)

    def test_report_skips_malformed_lines(self) -> None:
        gates.log_hit(self.p, "K3", "block", "block", "cli", "check", "a.md", "d")
        with open(os.path.join(self.root, gates.LOG_REL), "a") as f:
            f.write("garbage\n{\"x\": 1}\n")
        rc, out, _ = run_keel(self.root, "gate", "report")
        self.assertEqual(rc, 0)
        self.assertRegex(out, r"K3\s+1")


if __name__ == "__main__":
    unittest.main()
