import os
import tempfile
import unittest
from typing import Any

from helpers import make_project, run_keel
from keellib import render, store
from keellib.store import Project

TASKS_MD = "docs/devdocs/04-dev-tasks.md"
BACKLOG_MD = "docs/devdocs/backlog.md"
HEAD = "# 开发任务\n\n人写的前言\n\n"
TAIL = "\n## 备注\n人写的尾部\n"


def tk(n: int, **kw: Any) -> "dict[str, Any]":
    t: dict[str, Any] = {"id": f"T-{n}", "title": f"任务{n}", "status": "待开发", "review_profile": "fast",
                           "depends_on": [], "milestone": None, "record": None}
    t.update(kw)
    return t


class RenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_project(self._tmp.name)
        self.assertEqual(run_keel(self.root, "init")[0], 0)

    def path(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def read(self, rel: str) -> str:
        with open(self.path(rel), encoding="utf-8") as f:
            return f.read()

    def write(self, rel: str, text: str) -> None:
        with open(self.path(rel), "w", encoding="utf-8") as f:
            f.write(text)

    def seed_ledger(self) -> None:
        self.write(TASKS_MD, HEAD + render.BEGIN + "\n(空)\n" + render.END + "\n" + TAIL)

    def add(self, title: str, *extra: str) -> None:
        self.assertEqual(run_keel(self.root, "task", "add", "--title", title, "--source", "dev-tasks", *extra)[0], 0)

    def violations(self) -> "list[str]":
        return store.integrity_violations(Project.find(self.root))

    def test_region_only_changed_outside_bytes_kept(self) -> None:
        self.seed_ledger()
        self.add("第一张")
        text = self.read(TASKS_MD)
        self.assertTrue(text.startswith(HEAD + render.BEGIN))
        self.assertTrue(text.endswith(render.END + "\n" + TAIL))
        self.assertIn("| T-1 | 第一张 | 待开发 | fast | — | — | — |", text)
        self.assertNotIn("(空)", text)
        self.assertEqual(self.violations(), [])

    def test_archived_hidden_and_counted(self) -> None:
        self.seed_ledger()
        self.add("甲")
        self.add("乙")
        self.assertEqual(run_keel(self.root, "task", "archive", "T-1")[0], 0)
        text = self.read(TASKS_MD)
        self.assertNotIn("| T-1 |", text)
        self.assertIn("| T-2 |", text)
        self.assertIn("已归档 1 张，定义见 [archive/04-dev-tasks-archive.md](archive/04-dev-tasks-archive.md)", text)

    def test_ledger_region_format(self) -> None:
        r = render.ledger_region({"T-10": tk(10, title="a|b", depends_on=["T-2", "T-3"], milestone="M-1",
                                             record="audit/T-10/"), "T-2": tk(2)})
        lines = r.strip("\n").split("\n")
        self.assertEqual(lines[0], "| 编号 | 标题 | 状态 | profile | 依赖 | 里程碑 | 记录 |")
        self.assertTrue(lines[2].startswith("| T-2 |"))  # 数值升序
        self.assertEqual(lines[3], r"| T-10 | a\|b | 待开发 | fast | T-2, T-3 | M-1 | [记录](audit/T-10/) |")

    def test_line_cap(self) -> None:
        deps = [f"T-{100 + i}" for i in range(30)]
        r = render.ledger_region({"T-1": tk(1, title="长" * 80, depends_on=deps)})
        self.assertTrue(all(len(x) <= 500 for x in r.split("\n")))
        b = render.backlog_md({"F-01#1": {"source_id": "F-01", "entry_no": 1, "status": "parked",
                                          "note": "字" * 200, "detail": "backlog/F-01-1.md"}})
        self.assertTrue(all(len(x) <= 500 for x in b.split("\n")))

    def test_hand_edit_region_detected(self) -> None:
        self.seed_ledger()
        self.add("甲")
        self.write(TASKS_MD, self.read(TASKS_MD).replace("甲", "乙"))
        self.assertEqual(self.violations(), [render.REGION_KEY])

    def test_edit_outside_region_ok(self) -> None:
        self.seed_ledger()
        self.add("甲")
        self.write(TASKS_MD, self.read(TASKS_MD).replace("人写的前言", "改过的前言"))
        self.assertEqual(self.violations(), [])
        self.add("乙")  # 仍可写，且外部改动保留
        self.assertIn("改过的前言", self.read(TASKS_MD))

    def test_markers_removed_is_violation(self) -> None:
        self.seed_ledger()
        self.add("甲")
        self.write(TASKS_MD, "# 全删了\n")
        self.assertEqual(self.violations(), [render.REGION_KEY])

    def test_tasks_md_never_whole_file_in_manifest(self) -> None:
        self.seed_ledger()
        self.add("甲")
        man = Project.find(self.root).manifest()
        self.assertIn(render.REGION_KEY, man)
        self.assertNotIn(TASKS_MD, man)

    def test_no_markers_exit3(self) -> None:
        self.write(TASKS_MD, "# 没有标记\n")
        rc, _, err = run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")
        self.assertEqual(rc, 3)
        self.assertIn("keel migrate", err)
        self.assertEqual(self.read(TASKS_MD), "# 没有标记\n")
        self.assertEqual(os.listdir(self.path("docs/devdocs/state/tasks")), [])

    def test_duplicate_markers_exit3_nothing_written(self) -> None:
        self.write(TASKS_MD, render.BEGIN + render.BEGIN + render.END + "\n")
        rc, _, err = run_keel(self.root, "task", "add", "--title", "x", "--source", "dev-tasks")
        self.assertEqual(rc, 3)
        self.assertIn("重复或顺序不对", err)
        self.assertEqual(os.listdir(self.path("docs/devdocs/state/tasks")), [])
        self.write(TASKS_MD, render.END + render.BEGIN + "\n")
        self.assertEqual(run_keel(self.root, "render")[0], 3)

    def test_injection_rejected(self) -> None:
        self.seed_ledger()
        for bad in ("a\nb", "a\rb", "x " + render.END):
            rc, _, _ = run_keel(self.root, "task", "add", "--title", bad, "--source", "dev-tasks")
            self.assertEqual(rc, 1, bad)
        rc, _, _ = run_keel(self.root, "task", "add", "--title", "ok", "--source", "dev-tasks", "--milestone", "M\n1")
        self.assertEqual(rc, 1)
        rc, _, _ = run_keel(self.root, "backlog", "park", "F-01", "--note", "a\nb", "--by", "verify")
        self.assertEqual(rc, 1)
        self.assertEqual(os.listdir(self.path("docs/devdocs/state/tasks")), [])

    def test_symlinked_targets_refused(self) -> None:
        outside = os.path.join(self._tmp.name + "-out")
        os.makedirs(outside, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        target = os.path.join(outside, "victim.md")
        with open(target, "w", encoding="utf-8") as f:
            f.write("orig")
        os.symlink(target, self.path(BACKLOG_MD))
        rc, _, _ = run_keel(self.root, "backlog", "park", "F-01", "--note", "n", "--by", "verify")
        self.assertEqual(rc, 3)
        self.assertEqual(run_keel(self.root, "render")[0], 3)
        self.assertEqual(os.listdir(self.path("docs/devdocs/state/backlog")), [])
        with open(target, encoding="utf-8") as f:
            self.assertEqual(f.read(), "orig")
        os.remove(self.path(BACKLOG_MD))
        # devdocs 目录整体换成符号链接
        real = self.path("docs/devdocs")
        os.rename(real, real + ".bak")
        os.symlink(outside, real)
        p = Project.find(self.root)
        with p.lock(), self.assertRaises(store.KeelError) as cm:
            store.write_atomic(p, BACKLOG_MD, b"x")
        self.assertEqual(cm.exception.code, 3)
        self.assertFalse(os.path.exists(os.path.join(outside, "backlog.md")))

    def test_missing_tasks_md_skipped(self) -> None:
        self.add("甲")
        self.assertFalse(os.path.exists(self.path(TASKS_MD)))

    def test_backlog_md(self) -> None:
        run_keel(self.root, "backlog", "park", "F-01", "--note", "先放着", "--by", "verify")
        run_keel(self.root, "backlog", "park", "F-02", "--note", "关掉", "--by", "verify")
        run_keel(self.root, "backlog", "close", "F-02#1", "--reason", "不做了")
        text = self.read(BACKLOG_MD)
        self.assertIn("generated_by: keel", text)
        self.assertIn("spec_version: backlog.v3", text)
        self.assertIn("改状态用 `keel backlog …`", text)
        self.assertLess(text.index("### parked"), text.index("### closed"))
        self.assertIn("- F-01#1 · 先放着", text)
        self.assertEqual(self.violations(), [])
        self.write(BACKLOG_MD, text + "手改\n")
        self.assertEqual(self.violations(), [BACKLOG_MD])

    def test_backlog_detail_link(self) -> None:
        b = render.backlog_md({"F-01#1": {"source_id": "F-01", "entry_no": 1, "status": "parked",
                                          "note": "n", "detail": "backlog/F-01-1.md"},
                               "F-01#2": {"source_id": "F-01", "entry_no": 2, "status": "parked",
                                          "note": "m", "detail": None}})
        self.assertIn("- F-01#1 · n · [详情](backlog/F-01-1.md)", b)
        self.assertIn("- F-01#2 · m\n", b)

    def test_no_backlog_entries_no_file(self) -> None:
        self.add("甲")
        self.assertFalse(os.path.exists(self.path(BACKLOG_MD)))

    def test_render_cmd_idempotent_no_rewrite(self) -> None:
        self.seed_ledger()
        self.add("甲")
        run_keel(self.root, "backlog", "park", "F-01", "--note", "n", "--by", "verify")
        ino = [os.stat(self.path(p)).st_ino for p in (TASKS_MD, BACKLOG_MD)]
        self.assertEqual(run_keel(self.root, "render")[0], 0)
        self.assertEqual(ino, [os.stat(self.path(p)).st_ino for p in (TASKS_MD, BACKLOG_MD)])

    def test_render_cmd_records_missing_region_key(self) -> None:
        self.seed_ledger()
        self.add("甲")
        p = Project.find(self.root)
        m = p.manifest()
        del m[render.REGION_KEY]
        p.save_manifest(m)
        self.assertEqual(run_keel(self.root, "render")[0], 0)
        self.assertIn(render.REGION_KEY, p.manifest())

    def test_render_cmd_refuses_unmigrated(self) -> None:
        root = make_project(tempfile.mkdtemp(dir=self._tmp.name))
        self.assertEqual(run_keel(root, "render")[0], 3)


if __name__ == "__main__":
    unittest.main()
