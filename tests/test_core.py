import unittest

from wrapfit.core import check, find_violations


class FindViolationsTests(unittest.TestCase):
    def test_no_violations_when_everything_fits(self) -> None:
        text = "a short line\nanother short line"
        self.assertEqual(find_violations(text, width=20), [])

    def test_flags_word_longer_than_width(self) -> None:
        text = "see the report at\nhttps://example.com/reports/very-long-quarterly-summary-2026\nfor details."
        violations = find_violations(text, width=50)
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v.line, 2)
        self.assertEqual(v.length, 60)
        self.assertEqual(v.excess, 10)

    def test_all_lines_in_one_block_share_a_paragraph_number(self) -> None:
        text = "fine\nalsofine\nway-too-long-a-single-token-for-this-width"
        violations = find_violations(text, width=10)
        self.assertEqual([v.paragraph for v in violations], [1])

    def test_blank_line_starts_a_new_paragraph(self) -> None:
        text = "short line\n\nway-too-long-a-single-token-for-this-width\n\nshort again"
        violations = find_violations(text, width=10)
        self.assertEqual([v.line for v in violations], [3])
        self.assertEqual([v.paragraph for v in violations], [2])

    def test_multiple_blank_lines_only_count_as_one_paragraph_break(self) -> None:
        text = "first\n\n\n\nway-too-long-a-single-token-for-this-width"
        violations = find_violations(text, width=10)
        self.assertEqual([v.paragraph for v in violations], [2])

    def test_leading_blank_lines_do_not_create_an_empty_paragraph(self) -> None:
        text = "\n\nway-too-long-a-single-token-for-this-width"
        violations = find_violations(text, width=10)
        self.assertEqual([v.paragraph for v in violations], [1])

    def test_line_numbers_are_one_indexed_and_per_line(self) -> None:
        text = "fine\nalsofine\nway-too-long-a-single-token-for-this-width"
        violations = find_violations(text, width=10)
        self.assertEqual([v.line for v in violations], [3])

    def test_leading_tab_reduces_the_budget_for_that_line(self) -> None:
        # One tab at tabsize 4 expands to 4 columns, leaving 6 of the 10 for content.
        text = "\tabcdefghij"
        violations = find_violations(text, width=10, tabsize=4)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].excess, 4)

    def test_same_line_fits_without_tab_expansion(self) -> None:
        # Same word, but a width-10 budget with no leading tab: it fits exactly.
        text = "abcdefghij"
        self.assertEqual(find_violations(text, width=10, tabsize=4), [])

    def test_default_tabsize_is_eight(self) -> None:
        text = "\tabcdefghij"
        violations = find_violations(text, width=10)
        self.assertEqual(violations[0].excess, 8)

    def test_indent_wider_than_width_still_flags_any_word(self) -> None:
        text = "\t\t\tx"
        violations = find_violations(text, width=4, tabsize=4)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].excess, 1)


class CheckTests(unittest.TestCase):
    def test_strict_mode_fails_on_violation(self) -> None:
        report = check("supercalifragilisticexpialidocious", width=10)
        self.assertFalse(report.ok)
        self.assertEqual(len(report.violations), 1)
        self.assertIsNone(report.wrapped_line_count)

    def test_lenient_mode_reports_but_does_not_fail(self) -> None:
        report = check("supercalifragilisticexpialidocious", width=10, lenient=True)
        self.assertTrue(report.ok)
        self.assertEqual(len(report.violations), 1)
        self.assertIsNotNone(report.wrapped_line_count)
        self.assertGreater(report.wrapped_line_count, 1)

    def test_rejects_width_below_one(self) -> None:
        with self.assertRaises(ValueError):
            check("hello", width=0)

    def test_rejects_tabsize_below_one(self) -> None:
        with self.assertRaises(ValueError):
            check("hello", width=10, tabsize=0)

    def test_tabsize_is_passed_through_to_violation_detection(self) -> None:
        report = check("\tabcdefghij", width=10, tabsize=4)
        self.assertFalse(report.ok)
        self.assertEqual(report.violations[0].excess, 4)


class ReportToDictTests(unittest.TestCase):
    def test_dict_has_no_violations_and_null_line_count_when_fitting(self) -> None:
        report = check("a short line", width=20)
        self.assertEqual(
            report.to_dict(),
            {
                "ok": True,
                "width": 20,
                "lenient": False,
                "tabsize": 8,
                "violations": [],
                "wrapped_line_count": None,
            },
        )

    def test_dict_serializes_each_violation_as_a_plain_object(self) -> None:
        report = check("supercalifragilisticexpialidocious", width=10)
        d = report.to_dict()
        self.assertFalse(d["ok"])
        self.assertEqual(
            d["violations"],
            [
                {
                    "line": 1,
                    "paragraph": 1,
                    "word": "supercalifragilisticexpialidocious",
                    "length": 35,
                    "excess": 25,
                }
            ],
        )

    def test_dict_reports_wrapped_line_count_in_lenient_mode(self) -> None:
        report = check("supercalifragilisticexpialidocious", width=10, lenient=True)
        d = report.to_dict()
        self.assertTrue(d["ok"])
        self.assertIsNotNone(d["wrapped_line_count"])

    def test_dict_is_json_serializable(self) -> None:
        import json

        report = check("supercalifragilisticexpialidocious", width=10, lenient=True)
        # Round-tripping through json.dumps/loads should not raise or change the shape.
        self.assertEqual(json.loads(json.dumps(report.to_dict())), report.to_dict())


if __name__ == "__main__":
    unittest.main()
