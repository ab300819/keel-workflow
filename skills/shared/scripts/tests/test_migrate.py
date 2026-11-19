import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from helpers import CLEAN_ENV, SCRIPTS, git, make_project, run_keel

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "migrate")
LINT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS))), "skills", "pipeline", "scripts",
                    "health-lint.py")
REPORT = ".keel/migration-report.md"
MAP = ["--map-status", "🔍 待审查=review_pending"]
ROLLBACK = "git checkout -- docs/devdocs && git clean -fd docs/devdocs && rm -rf docs/devdocs/state .keel/manifest.json"


def section(report: str, name: str) -> str:
    return report.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0]


class MigrateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = make_project(self._tmp.name, commit=False)

    def load(self, name: str) -> None:
        shutil.copytree(os.path.join(FIX, name, "docs"), os.path.join(self.root, "docs"), dirs_exist_ok=True)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "snap")

    def read(self, rel: str) -> str:
        with open(os.path.join(self.root, rel), encoding="utf-8") as f:
            return f.read()

    def snapshot(self) -> "dict[str, bytes]":
        out = {}
        for d, _dirs, files in os.walk(os.path.join(self.root, "docs")):
            for f in files:
                p = os.path.join(d, f)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, self.root)] = fh.read()
        return out

    def commit(self) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "c")

    def migrate(self, *args: str) -> "tuple[int, str]":
        rc, out, err = run_keel(self.root, "migrate", *args)
        return rc, self.read(REPORT) if os.path.exists(os.path.join(self.root, REPORT)) else out + err

    def task_count(self) -> int:
        rc, out, _ = run_keel(self.root, "task", "list")
        self.assertEqual(rc, 0)
        return len([x for x in out.splitlines() if x and not x.startswith("#")])

    def test_keel_template_dry_run(self) -> None:
        self.load("keel-template")
        rc, rep = self.migrate()
        self.assertEqual(rc, 0, rep)
        self.assertIn("- 任务：3", section(rep, "已迁移"))
        self.assertIn("（无）", section(rep, "未识别"))
        self.assertIn("（无）", section(rep, "待映射状态"))
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs/devdocs/state")))

    def test_keel_template_apply(self) -> None:
        self.load("keel-template")
        rc, rep = self.migrate("--apply")
        self.assertEqual(rc, 0, rep)
        text = self.read("docs/devdocs/04-dev-tasks.md")
        self.assertIn("spec_version: tasks.v3", text)
        self.assertNotIn("| **状态** |", text)
        self.assertNotIn("| **commits** |", text)
        self.assertIn("| **描述** | 计价规则与折扣 |", text)
        self.assertIn("<!-- keel:begin ledger -->", text)
        self.assertIn("| T-02 | 实现计价服务 | 进行中 | audit |", text)
        self.assertIn("| T-02 | 折扣叠加顺序 | 用例覆盖 |", text)  # 风险表不是状态表，保留
        self.assertIn("| T-99 | 围栏里的表格不解析 |", text)
        self.assertNotIn("| T-01: 建立数据表 | ⚪ |", text)
        _, out, _ = run_keel(self.root, "task", "get", "T-01")
        self.assertIn('"ref": "app@1a2b3c4d"', out)
        self.assertIn("<repository>@<full-sha>", self.read("docs/devdocs/audit/T-02/ledger-record.md"))
        self.assertEqual(self.task_count(), 3)
        rc, out, err = run_keel(self.root, "check")
        self.assertNotIn("K1", out + err)
        self.assertNotIn("K2", out + err)

    def test_aicode_dry_run_reports(self) -> None:
        self.load("aicode-shape")
        rc, rep = self.migrate("--dry-run")
        self.assertEqual(rc, 0, rep)
        pend = section(rep, "待映射状态")
        self.assertIn("`🔍 待审查` → 3", pend)
        self.assertIn("`关闭` → 1", pend)  # 编号单元格后缀里的状态，日期括号去掉
        unk = section(rep, "未识别")
        for s in ("backlog/M-003-9.md:1", "T-12a", "T-RF-1", "T-14"):
            self.assertIn(s, unk)
        for s in ("T-20", "T-22", "T-23"):
            self.assertNotIn(s, unk)
        self.assertIn("T-13", section(rep, "状态冲突"))

    def test_apply_refused_without_map(self) -> None:
        self.load("aicode-shape")
        before = self.snapshot()
        rc, rep = self.migrate("--apply")
        self.assertEqual(rc, 1)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs/devdocs/state")))
        rc, _ = self.migrate("--apply", *MAP)  # 仍有未识别，无 --allow-partial 也拒绝
        self.assertEqual(rc, 1)
        self.assertEqual(self.snapshot(), before)

    def test_apply_partial(self) -> None:
        self.load("aicode-shape")
        rc, rep = self.migrate("--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 0, rep)
        rec = self.read("docs/devdocs/audit/T-10/ledger-record.md")
        self.assertIn("## 迁移自 04-dev-tasks.md（", rec)
        self.assertEqual(rec.count("合成长备注：本段文字"), 18)
        migrated = section(rep, "已迁移")
        n = int(migrated.split("- 任务：")[1].split("\n")[0])
        self.assertEqual(self.task_count(), n)
        _, out, _ = run_keel(self.root, "task", "get", "T-11")
        self.assertIn("…", out)
        self.assertIn('"status": "进行中"', out)
        _, out, _ = run_keel(self.root, "task", "get", "T-10")
        self.assertIn('"ext_review_state": "EXT_UNRESOLVED"', out)
        self.assertIn('"status": "已完成"', out)
        text = self.read("docs/devdocs/04-dev-tasks.md")
        self.assertIn("| T-12a | 带字母后缀的编号 |", text)  # 未识别的行原样留在生成区外
        self.assertIn("| T-24 🔍 待审查 | 待审查的 audit 任务 |", text)
        self.assertNotIn("| T-20 ✅ |", text)
        for tid, st in (("T-20", "已完成"), ("T-22", "已完成"), ("T-13", "待开发")):
            self.assertIn(f'"status": "{st}"', run_keel(self.root, "task", "get", tid)[1], tid)
        self.assertIn('"title": "旧口径表里的任务"', run_keel(self.root, "task", "get", "T-20")[1])
        for tid, why in (("T-12", "deferred-fast"), ("T-23", "deferred-guarded")):
            out = run_keel(self.root, "task", "get", tid)[1]
            self.assertIn('"status": "review_pending"', out)
            self.assertIn('"batch": "migrated-v3"', out)
            self.assertIn(f'"pending_reason": "{why}"', out)
        self.assertEqual(run_keel(self.root, "task", "get", "T-24")[0], 1)
        rp = section(rep, "review_pending 补字段")
        self.assertIn("T-12", rp)
        self.assertIn("T-23", rp)
        self.assertIn("audit", section(rep, "待映射状态"))
        arch = self.read("docs/devdocs/audit/migration-v3.md")
        for s in ("| ID | 描述 | 状态 |", "| # | 任务 | 层 |", "| T-20 ✅ |", "合成长备注：本段文字"):
            self.assertIn(s, arch)
        self.assertTrue(rep.rstrip().endswith(ROLLBACK + "`"))
        self.assertNotIn("| T-13 | 分册任务 | 待开发 |", text)
        self.assertIn("人写的正文保留。", text)
        self.assertIn("spec_version: backlog.v3", self.read("docs/devdocs/backlog.md"))
        self.assertIn("# DevDocs Backlog", self.read("docs/devdocs/backlog/index.md"))  # 原 backlog.md 另存
        self.assertIn("backlog.md 原文 → backlog/index.md", rep)
        _, out, _ = run_keel(self.root, "backlog", "get", "T-26#1")
        self.assertIn('"note": "用 id 键且没写 note 的条目"', out)
        self.assertIn('"detail": "backlog/T-26-1.md"', out)
        rc, out, err = run_keel(self.root, "check")
        self.assertNotIn("K1", out + err)
        self.assertNotIn("K2", out + err)
        with open(os.path.join(self.root, "docs/devdocs/99-unregistered.md"), "w", encoding="utf-8") as f:
            f.write("x\n")
        p = subprocess.run([sys.executable, LINT, "--target", self.root], capture_output=True, text=True, env=CLEAN_ENV)
        self.assertIn("docs/devdocs/99-unregistered.md", p.stdout)  # 未登记路径照常报，证明规则在跑
        unknown = [b for b in p.stdout.split("- rule_id:") if b.strip().startswith("layout/unknown-path")]
        self.assertFalse([b for b in unknown if "docs/devdocs/state/" in b or "docs/devdocs/audit/" in b])
        os.remove(os.path.join(self.root, "docs/devdocs/99-unregistered.md"))
        self.commit()
        rc, rep = self.migrate("--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 0, rep)
        self.assertEqual(self.read("docs/devdocs/audit/T-10/ledger-record.md"), rec)
        self.assertEqual(self.read("docs/devdocs/audit/migration-v3.md"), arch)
        self.assertEqual(self.task_count(), n)

    def test_existing_ledger_text_not_appended(self) -> None:
        self.load("aicode-shape")
        rec = os.path.join(self.root, "docs/devdocs/audit/T-10/ledger-record.md")
        os.makedirs(os.path.dirname(rec))
        text = self.read("docs/devdocs/04-dev-tasks.md")
        note = next(c for c in text.split("|") if "合成长备注" in c).strip()
        with open(rec, "w", encoding="utf-8") as f:
            f.write("# 手工搬过\n\n" + note + "\n")
        self.commit()
        rc, rep = self.migrate("--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 0, rep)
        self.assertEqual(self.read("docs/devdocs/audit/T-10/ledger-record.md").count(note), 1)

    def test_migrated_markerless_gets_markers(self) -> None:
        self.assertEqual(run_keel(self.root, "init")[0], 0)
        self.assertEqual(run_keel(self.root, "task", "add", "--title", "已有", "--source", "dev-tasks")[0], 0)
        with open(os.path.join(self.root, "docs/devdocs/04-dev-tasks.md"), "w", encoding="utf-8") as f:
            f.write("# 任务\n\n| ID | 状态 | 备注 |\n|---|---|---|\n| T-1 | 待开发 | 旧备注 |\n\n"
                    "#### T-1: 已有\n\n| 属性 | 内容 |\n|---|---|\n| **状态** | 待开发 |\n")
        self.assertEqual(run_keel(self.root, "render")[0], 3)
        self.commit()
        rc, rep = self.migrate("--apply")
        self.assertEqual(rc, 0, rep)
        self.assertEqual(run_keel(self.root, "render")[0], 0)
        self.assertIn("| T-1 | 已有 | 待开发 |", self.read("docs/devdocs/04-dev-tasks.md"))
        self.assertEqual(self.task_count(), 1)
        self.assertIn("旧备注", self.read("docs/devdocs/audit/T-1/ledger-record.md"))
        self.assertNotIn("| T-1 | 待开发 | 旧备注 |", self.read("docs/devdocs/04-dev-tasks.md"))

    def test_dirty_docs_refused(self) -> None:
        self.load("aicode-shape")
        with open(os.path.join(self.root, "docs/devdocs/99-draft.md"), "w", encoding="utf-8") as f:
            f.write("未提交\n")
        rc, _, err = run_keel(self.root, "migrate", "--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 1)
        self.assertIn("docs/devdocs 有未提交改动，先提交或暂存再迁移", err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs/devdocs/state")))

    def test_rollback_recipe(self) -> None:
        self.load("aicode-shape")
        before = self.snapshot()
        self.assertEqual(self.migrate("--apply", "--allow-partial", *MAP)[0], 0)
        subprocess.run(["bash", "-c", ROLLBACK], cwd=self.root, check=True, env=CLEAN_ENV, capture_output=True)
        self.assertEqual(self.snapshot(), before)
        rc, rep = self.migrate("--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 0, rep)
        rc, out, err = run_keel(self.root, "check")
        self.assertNotIn("K1", out + err)

    def test_saved_tables_not_duplicated(self) -> None:
        self.load("aicode-shape")
        lines = self.read("docs/devdocs/04-dev-tasks.md").split("\n")
        a = next(i for i, x in enumerate(lines) if x.startswith("| ID | 描述"))
        b = next(i for i, x in enumerate(lines) if x.startswith("| T-RF-1"))
        table = "\n".join(lines[a:b + 1])
        path = os.path.join(self.root, "docs/devdocs/audit/migration-v3.md")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 已存\n\n" + table + "\n")
        self.commit()
        self.assertEqual(self.migrate("--apply", "--allow-partial", *MAP)[0], 0)
        self.assertEqual(self.read("docs/devdocs/audit/migration-v3.md").count(table), 1)

    def test_outside_git_keeps_hand_backlog(self) -> None:
        """I2：不在 git 里、backlog/index.md 已存在时，手写的 backlog.md 原文另存到 audit，报告不说「已提交」。"""
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root = make_project(t.name, git_repo=False)
        shutil.copytree(os.path.join(FIX, "aicode-shape", "docs"), os.path.join(root, "docs"), dirs_exist_ok=True)
        bl = os.path.join(root, "docs/devdocs/backlog.md")
        with open(bl, "a", encoding="utf-8") as f:
            f.write("\n手写说明：只在这里出现\n")
        with open(os.path.join(root, "docs/devdocs/backlog/index.md"), "w", encoding="utf-8") as f:
            f.write("# 已有索引\n")
        rc, out, err = run_keel(root, "migrate", "--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 0, err)
        with open(os.path.join(root, "docs/devdocs/audit/migration-v3-backlog.md"), encoding="utf-8") as f:
            self.assertIn("手写说明：只在这里出现", f.read())
        with open(os.path.join(root, REPORT), encoding="utf-8") as f:
            rep = f.read()
        self.assertIn("backlog.md 原文 → audit/migration-v3-backlog.md", rep)
        self.assertNotIn("已提交", rep)
        self.assertIn("没有回滚手段", rep)

    def test_symlink_checked_before_any_write(self) -> None:
        """M4：audit/ 是符号链接时，一个状态文件都不写。"""
        self.load("aicode-shape")
        elsewhere = tempfile.mkdtemp(dir=self._tmp.name)
        os.symlink(elsewhere, os.path.join(self.root, "docs/devdocs/audit"))
        self.commit()
        rc, _, err = run_keel(self.root, "migrate", "--apply", "--allow-partial", *MAP)
        self.assertEqual(rc, 3)
        self.assertIn("符号链接", err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs/devdocs/state")))
        self.assertEqual(os.listdir(elsewhere), [])

    def test_bad_map_status(self) -> None:
        self.load("aicode-shape")
        rc, _, err = run_keel(self.root, "migrate", "--map-status", "🔍 待审查=审查中")
        self.assertEqual(rc, 2, err)


if __name__ == "__main__":
    unittest.main()
