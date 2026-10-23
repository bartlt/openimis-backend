"""Unit tests for compare.py. Run: python -m unittest discover -s tools/api_snapshot/tests"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import compare  # noqa: E402


def snap(name, response, status=200):
    return {"query": name, "screen": f"screen {name}", "http_status": status, "response": response}


def write(folder, snaps, django="4.2"):
    folder.mkdir()
    for s in snaps:
        (folder / f"{s['query']}.json").write_text(json.dumps(s))
    (folder / "_manifest.json").write_text(json.dumps({"versions": {"Django": django, "graphene": "x"}, "git": "abc"}))


class CompareTest(unittest.TestCase):
    def run_cli(self, before, after):
        """Run compare.py's main() on two lists of snapshots; return (exit code, stdout, html)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            write(tmp / "before", before)
            write(tmp / "after", after, django="5.2")
            report = tmp / "report.html"
            argv, sys.argv = sys.argv, ["compare.py", str(tmp / "before"), str(tmp / "after"), "--report", str(report)]
            out = io.StringIO()
            try:
                with redirect_stdout(out), self.assertRaises(SystemExit) as exit_:
                    compare.main()
            finally:
                sys.argv = argv
            return exit_.exception.code, out.getvalue(), report.read_text()

    def status(self, a, b):
        return compare.compare({"q": snap("q", a)}, {"q": snap("q", b)})[0]

    def test_identical(self):
        data = {"data": {"insurees": {"edges": [{"node": {"chfId": "070707070", "age": 1}}]}}}
        code, out, report = self.run_cli([snap("01_a", data), snap("02_b", {"data": {"x": None}})],
                                         [snap("01_a", data), snap("02_b", {"data": {"x": None}})])
        self.assertEqual(code, 0)
        self.assertIn("2 queries, 2 identical, 0 different (3 values compared)", out)
        self.assertIn("#15803d", report)  # green banner
        self.assertIn("Django 5.2", report)

    def test_key_order_ignored_list_order_not(self):
        self.assertEqual(self.status({"a": 1, "b": 2}, {"b": 2, "a": 1})["status"], "identical")
        row = self.status({"data": [1, 2]}, {"data": [2, 1]})
        self.assertEqual(row["status"], "different")
        self.assertEqual(row["changes"], [("response.data[0]", 1, 2), ("response.data[1]", 2, 1)])

    def test_changed_value(self):
        before = {"data": {"claim": {"code": "CIA00001", "attachmentsCount": 0}}}
        after = {"data": {"claim": {"code": "CIA00001", "attachmentsCount": 1}}}
        code, out, report = self.run_cli([snap("15_claim", before)], [snap("15_claim", after)])
        self.assertEqual(code, 1)
        self.assertIn("1 queries, 0 identical, 1 different", out)
        self.assertIn("response.data.claim.attachmentsCount", report)
        self.assertIn("#b91c1c", report)  # red banner

    def test_type_change(self):
        for old, new in [(1, 1.0), (1, "1"), (True, 1), (0, False), ("4.00", 4.0), (None, "")]:
            with self.subTest(old=old, new=new):
                row = self.status({"v": old}, {"v": new})
                self.assertEqual(row["status"], "different")
                self.assertEqual(row["changes"], [("response.v", old, new)])

    def test_missing_key(self):
        row = self.status({"data": {"a": 1, "b": 2}}, {"data": {"a": 1}})
        self.assertEqual(row["changes"], [("response.data.b", 2, "(missing)")])
        row = self.status({"data": {"a": 1}}, {"data": {"a": 1, "c": 3}})
        self.assertEqual(row["changes"], [("response.data.c", "(missing)", 3)])

    def test_missing_query_file(self):
        rows = compare.compare({"q": snap("q", {})}, {})
        self.assertEqual(rows[0]["status"], "only in before")

    def test_errors_fail_even_if_identical(self):
        failing = {"data": None, "errors": [{"message": "boom"}]}
        code, out, _ = self.run_cli([snap("q", failing)], [snap("q", failing)])
        self.assertEqual(code, 1)
        self.assertIn("FAILS IN BOTH", out)
        self.assertEqual(self.status(failing, failing)["status"], "fails in both")

    def test_errors_on_one_side(self):
        ok = {"data": {"a": 1}}
        failing = {"data": {"a": 1}, "errors": [{"message": "boom"}]}
        code, _, _ = self.run_cli([snap("q", ok)], [snap("q", failing)])
        self.assertEqual(code, 1)

    def test_non_json_body_fails(self):
        html_page = {"non_json_body": "<html>Server Error</html>"}
        self.assertEqual(self.status(html_page, html_page)["status"], "fails in both")

    def test_screen_label_not_compared(self):
        before, after = snap("q", {"data": {"a": 1}}), snap("q", {"data": {"a": 1}})
        after["screen"] = "renamed screen"
        self.assertEqual(compare.compare({"q": before}, {"q": after})[0]["status"], "identical")

    def test_http_status_change(self):
        rows = compare.compare({"q": snap("q", {}, 200)}, {"q": snap("q", {}, 500)})
        self.assertEqual(rows[0]["changes"][0], ("http_status", 200, 500))


if __name__ == "__main__":
    unittest.main()
