import unittest

import helpers
from keellib import schema


def task(**kw):
    t = schema.new_task("T-1", "标题", "dev-tasks")
    t.update(kw)
    return t


def errs(**kw):
    return schema.validate_task(task(**kw), {"T-1", "T-2"})


def backlog(**kw):
    e = schema.new_backlog("F-01", 1, "verify", "备注", "2026-11-19")
    e.update(kw)
    return e


class TaskTest(unittest.TestCase):
    def test_valid_default(self):
        self.assertEqual(errs(), [])

    def test_status_enum(self):
        self.assertTrue(errs(status="乱写"))

    def test_title_cap_counts_chars(self):
        self.assertEqual(errs(title="中" * 80), [])
        self.assertTrue(errs(title="中" * 81))

    def test_rendered_fields_capped(self):  # M1：进生成区的字段有上限，工具不会自己写出 K3 违规行
        for f, cap in (("milestone", 80), ("layer", 80), ("record", 200)):
            self.assertEqual(errs(**{f: "中" * cap}), [], f)
            self.assertTrue(errs(**{f: "中" * (cap + 1)}), f)

    def test_review_pending_needs_fields(self):
        full = dict(status="review_pending", batch="B1", due="2026-12-01", pending_reason="deferred-fast")
        self.assertEqual(errs(**full), [])
        for k in ("batch", "due", "pending_reason"):
            self.assertTrue(errs(**{**full, k: None}), k)

    def test_audit_done_needs_ext_review(self):
        self.assertTrue(errs(review_profile="audit", status="已完成"))
        self.assertEqual(errs(review_profile="audit", status="已完成", ext_review_state="EXT_REVIEWED"), [])

    def test_depends_on(self):
        self.assertTrue(errs(depends_on=["T-9"]))
        self.assertTrue(errs(depends_on=["T-1"]))
        self.assertEqual(errs(depends_on=["T-2"]), [])

    def test_derived_from(self):
        self.assertTrue(errs(derived_from="T-9"))
        self.assertEqual(errs(derived_from="T-2"), [])

    def test_commit_ref(self):
        self.assertTrue(errs(commits=[{"ref": "bad", "note": ""}]))
        self.assertEqual(errs(commits=[{"ref": "app@" + "a" * 40, "note": "x"}]), [])

    def test_move_profile_valid(self):
        self.assertEqual(schema.validate_task(schema.new_task("T-1", "t", "F-001", review_profile="move"), set()), [])

    def test_commit_kind_test_valid(self):
        self.assertEqual(errs(commits=[{"ref": "app@abcdef1", "note": "n", "kind": "test"}]), [])

    def test_commit_kind_unknown_rejected(self):
        self.assertIn("commits[].kind", errs(commits=[{"ref": "app@abcdef1", "note": "n", "kind": "code"}])[0])

    def test_source_empty(self):
        self.assertTrue(errs(source=""))

    def test_unknown_key(self):
        self.assertTrue(errs(titel="x"))

    def test_error_format(self):
        self.assertIn("；", errs(status="乱写")[0])


class BacklogTest(unittest.TestCase):
    def test_valid_default(self):
        self.assertEqual(schema.validate_backlog(backlog()), [])

    def test_bad_prefix(self):
        self.assertTrue(schema.validate_backlog(backlog(source_id="B-01")))

    def test_conditionals(self):
        v = schema.validate_backlog
        self.assertTrue(v(backlog(status="reactivated", target_flow="feature")))
        self.assertEqual(v(backlog(status="reactivated", target_flow="feature", target_id="F-02")), [])
        self.assertTrue(v(backlog(status="closed")))
        self.assertTrue(v(backlog(status="superseded")))

    def test_note_cap(self):
        self.assertEqual(schema.validate_backlog(backlog(note="中" * 200)), [])
        self.assertTrue(schema.validate_backlog(backlog(note="中" * 201)))

    def test_bad_entry_no_and_date(self):
        self.assertTrue(schema.validate_backlog(backlog(entry_no=0)))
        self.assertTrue(schema.validate_backlog(backlog(created_at="2026/11/19")))


class DescribeTest(unittest.TestCase):
    def test_describe_lists_all_fields(self):
        for kind, obj in (("task", task()), ("backlog", backlog())):
            out = schema.describe(kind)
            for f in obj:
                self.assertIn(f, out)

    def test_cli(self):
        code, out, _ = helpers.run_keel("/nonexistent", "schema", "task")
        self.assertEqual(code, 0)
        self.assertIn("review_profile", out)

    def test_trailing_newline_rejected(self):
        t = schema.new_task("T-1\n", "x", "dev-tasks")
        self.assertTrue(schema.validate_task(t, set()))
        t = schema.new_task("T-1", "x", "dev-tasks", commits=[{"ref": "r@abcdef1\n", "note": "n"}])
        self.assertTrue(schema.validate_task(t, set()))
        self.assertTrue(schema.validate_backlog(schema.new_backlog("F-01\n", 1, "v", "n", "2026-11-19")))
        self.assertTrue(schema.validate_backlog(schema.new_backlog("F-01", 1, "v", "n", "2026-11-19\n")))


if __name__ == "__main__":
    unittest.main()
