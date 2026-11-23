import os
import tempfile
import unittest

import helpers
from keellib import movecheck


def diff(*files: "tuple[str, list[str], list[str]]") -> str:
    out = []
    for path, dels, adds in files:
        out += [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}", "@@ -1 +1 @@"]
        out += ["-" + d for d in dels] + ["+" + a for a in adds]
    return "\n".join(out) + "\n"


class FindGlueTest(unittest.TestCase):
    def test_pure_move_across_files_no_glue(self) -> None:
        lines = ["a = 1", "b = g(a)", "c = h(b)"]
        self.assertEqual(movecheck.find_glue(diff(("a.py", lines, []), ("b.py", [], lines))), (3, []))

    def test_indent_only_move_has_no_glue(self) -> None:
        self.assertEqual(movecheck.find_glue(diff(("a.py", ["    x = f(y)"], ["        x = f(y)"]))), (1, []))

    def test_signature_glue_not_logic(self) -> None:
        _, glue = movecheck.find_glue(diff(("a.py", [], ["def helper(a, b):", "helper(a, b)"])))
        self.assertEqual(len(glue), 2)
        self.assertFalse(any(g.logic for g in glue))

    def test_condition_change_is_logic(self) -> None:
        _, glue = movecheck.find_glue(diff(("a.py", ["if a > b:"], ["if a >= b:"])))
        self.assertEqual(len(glue), 2)
        self.assertTrue([g for g in glue if g.sign == "+"][0].logic)

    def test_literal_change_is_logic(self) -> None:
        _, glue = movecheck.find_glue(diff(("a.py", ["x = 3"], ["x = 4"])))
        self.assertTrue(any(g.logic for g in glue))

    def test_import_lines_not_logic(self) -> None:
        _, glue = movecheck.find_glue(diff(("a.ts", [], ["import { a } from './a'"])))
        self.assertEqual(len(glue), 1)
        self.assertFalse(glue[0].logic)

    def test_cli_reports_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = helpers.make_project(tmp)
            with open(os.path.join(root, "a.py"), "w") as f:
                f.write("def f(x):\n    y = x + z\n    w = y * q\n")
            helpers.git(root, "add", "-A")
            helpers.git(root, "commit", "-qm", "a")
            os.remove(os.path.join(root, "a.py"))
            with open(os.path.join(root, "b.py"), "w") as f:
                f.write("def f(x):\n    y = x + z\n    w = y * q\n    return 1\n")
            helpers.git(root, "add", "-A")
            helpers.git(root, "commit", "-qm", "b")
            rc, out, _ = helpers.run_keel(root, "move-check", "HEAD~1..HEAD")
        self.assertEqual(rc, 0)
        self.assertIn("胶水", out)
        self.assertNotIn("搬动 0 行", out)
        self.assertIn("return 1", out)


if __name__ == "__main__":
    unittest.main()
