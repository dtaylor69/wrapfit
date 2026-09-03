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


if __name__ == "__main__":
    unittest.main()
