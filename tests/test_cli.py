import contextlib
import io
import json
import os
import tempfile
import unittest

from wrapfit.cli import main


def run(argv, stdin_text=""):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stdin(io.StringIO(stdin_text)):
        code = main(argv)
    return code, out.getvalue()


def write(root, relpath, content):
    path = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


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


class ParagraphReportingTests(unittest.TestCase):
    def test_text_output_reports_paragraph_number_for_prose(self) -> None:
        text = (
            "first paragraph, all fine.\n"
            "\n"
            "second paragraph has a supercalifragilisticexpialidocious word.\n"
        )
        code, out = run(["-w", "20"], stdin_text=text)
        self.assertEqual(code, 1)
        self.assertIn("line 3, paragraph 2:", out)

    def test_json_output_includes_paragraph_per_violation(self) -> None:
        text = "fine\n\nsupercalifragilisticexpialidocious\n"
        code, out = run(["-w", "10", "--json"], stdin_text=text)
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["violations"][0]["paragraph"], 2)


class DirectoryModeTests(unittest.TestCase):
    def test_fitting_directory_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            write(root, "a.txt", "a short line\n")
            write(root, "sub/b.txt", "another short line\n")
            code, out = run([root, "-w", "20"])
            self.assertEqual(code, 0)
            self.assertIn("2 file(s)", out)

    def test_reports_violations_prefixed_with_path(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            good = write(root, "good.txt", "fine\n")
            bad = write(root, "bad.txt", "supercalifragilisticexpialidocious\n")
            code, out = run([root, "-w", "10"])
            self.assertEqual(code, 1)
            self.assertIn(f"{bad}:1, paragraph 1:", out)
            self.assertNotIn(good, out)

    def test_json_output_is_a_list_with_path_per_entry(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = write(root, "notes.txt", "supercalifragilisticexpialidocious\n")
            code, out = run([root, "-w", "10", "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(out)
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["path"], path)
            self.assertFalse(payload[0]["ok"])

    def test_lenient_directory_mode_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            write(root, "notes.txt", "supercalifragilisticexpialidocious\n")
            code, _ = run([root, "-w", "10", "--lenient"])
            self.assertEqual(code, 0)

    def test_binary_file_is_skipped_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            write(root, "fine.txt", "fine\n")
            with open(os.path.join(root, "blob.bin"), "wb") as f:
                f.write(bytes(range(256)))
            code, out = run([root, "-w", "20"])
            self.assertEqual(code, 0)
            self.assertIn("1 file(s)", out)


if __name__ == "__main__":
    unittest.main()
