import contextlib
import io
import json
import unittest

from wrapfit.cli import main


def run(argv, stdin_text=""):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stdin(io.StringIO(stdin_text)):
        code = main(argv)
    return code, out.getvalue()


class JsonOutputTests(unittest.TestCase):
    def test_json_output_on_fitting_text_is_ok_and_exits_zero(self) -> None:
        code, out = run(["-w", "20", "--json"], stdin_text="a short line\n")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["violations"], [])

    def test_json_output_reports_violation_and_exits_one(self) -> None:
        code, out = run(["-w", "10", "--json"], stdin_text="supercalifragilisticexpialidocious\n")
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(len(payload["violations"]), 1)
        self.assertEqual(payload["violations"][0]["word"], "supercalifragilisticexpialidocious")

    def test_json_output_in_lenient_mode_is_ok_but_still_lists_violations(self) -> None:
        code, out = run(["-w", "10", "--lenient", "--json"], stdin_text="supercalifragilisticexpialidocious\n")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["lenient"])
        self.assertEqual(len(payload["violations"]), 1)
        self.assertIsNotNone(payload["wrapped_line_count"])

    def test_json_output_is_a_single_line(self) -> None:
        _, out = run(["-w", "20", "--json"], stdin_text="a short line\n")
        self.assertEqual(out.count("\n"), 1)


if __name__ == "__main__":
    unittest.main()
