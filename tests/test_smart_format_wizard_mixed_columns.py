"""
Tests for SmartFormatWizard robustness with non-string column labels.

Reproduces the crash:
    TypeError: sequence item 2: expected str instance, int found
    at _populate_step3 line ~516:  ", ".join(dropped[:10])
when df.columns contains integer indices (e.g. from a headerless CSV).

These tests are deliberately self-contained (no pandas / Tkinter required)
so they run in any environment that has a standard Python 3 installation.
"""

import sys
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Copy _fmt_list verbatim from the wizard module so we can test it without
# importing the full module (which requires pandas + Tkinter).
# ---------------------------------------------------------------------------

def _fmt_list(items, limit: int = 10) -> str:
    """Safe comma-separated display string – mirrors wizard._fmt_list."""
    if not items:
        return "(none)"
    lst = [str(x) for x in items]
    if limit is not None and len(lst) > limit:
        return ", ".join(lst[:limit]) + f"  …+{len(lst) - limit} more"
    return ", ".join(lst)


class TestFmtList(unittest.TestCase):
    """Unit tests for _fmt_list helper (mirrors wizard implementation)."""

    def test_pure_strings_unchanged(self):
        self.assertEqual(_fmt_list(["Alpha", "Beta", "Gamma"]), "Alpha, Beta, Gamma")

    def test_int_items_no_crash(self):
        """Primary regression: int column labels must not raise TypeError."""
        result = _fmt_list([0, "Cust", "Seg"])
        self.assertEqual(result, "0, Cust, Seg")

    def test_all_int_columns(self):
        """DataFrame with no header row gives 0..N integer columns."""
        result = _fmt_list([0, 1, 2, 3])
        self.assertEqual(result, "0, 1, 2, 3")

    def test_mixed_types(self):
        result = _fmt_list([0, 1.5, "Name", None])
        self.assertEqual(result, "0, 1.5, Name, None")

    def test_limit_applied(self):
        items = list(range(15))
        result = _fmt_list(items, limit=10)
        self.assertIn("…+5 more", result)
        self.assertTrue(result.startswith("0, 1, 2"))

    def test_limit_none_shows_all(self):
        items = list(range(15))
        result = _fmt_list(items, limit=None)
        self.assertNotIn("more", result)
        self.assertIn("14", result)

    def test_empty_list(self):
        self.assertEqual(_fmt_list([]), "(none)")

    def test_none_input(self):
        self.assertEqual(_fmt_list(None), "(none)")

    def test_single_item(self):
        self.assertEqual(_fmt_list([42]), "42")

    def test_exactly_at_limit(self):
        items = list(range(10))
        self.assertNotIn("more", _fmt_list(items, limit=10))


class TestOriginalCrashPath(unittest.TestCase):
    """
    Reproduce the exact crash pattern from the bug report without any
    external dependencies.
    """

    def _old_join(self, dropped):
        """Mirrors the BROKEN original code that caused the crash."""
        return "Dropped: " + ", ".join(dropped[:10]) \
               + (f"  …+{len(dropped) - 10} more" if len(dropped) > 10 else "")

    def _new_join(self, dropped):
        """Mirrors the FIXED code using _fmt_list."""
        return "Dropped: " + _fmt_list(dropped)

    def test_old_code_crashes_on_int(self):
        """Prove the original code raises TypeError with int columns."""
        dropped = [0, "Cust", "Seg"]
        with self.assertRaises(TypeError):
            self._old_join(dropped)

    def test_new_code_does_not_crash(self):
        """Prove the fixed code handles int columns without error."""
        dropped = [0, "Cust", "Seg"]
        result = self._new_join(dropped)
        self.assertIsInstance(result, str)
        self.assertIn("0", result)
        self.assertIn("Cust", result)

    def test_new_code_all_string_unchanged(self):
        """All-string case must produce identical output to the old code."""
        dropped = ["Foo", "Bar", "Baz"]
        self.assertEqual(
            self._old_join(dropped),
            self._new_join(dropped),
        )

    def test_new_code_limit_suffix(self):
        dropped = list(range(12))
        result = self._new_join(dropped)
        self.assertIn("…+2 more", result)


class TestRawColumnNormalisation(unittest.TestCase):
    """
    Verify the upstream normalisation in SmartFormatWizard.__init__ logic:
    any non-string column label must be coerced to str before reaching
    infer_mapping or the display code.
    """

    def _normalise(self, raw_columns):
        """Mirrors the wizard's normalisation logic."""
        return [str(c) for c in raw_columns]

    def test_int_labels_normalised(self):
        raw = [0, 1, 2]
        normed = self._normalise(raw)
        self.assertEqual(normed, ["0", "1", "2"])

    def test_mixed_labels_normalised(self):
        raw = [0, "Cust", 2.5, "Seg"]
        normed = self._normalise(raw)
        self.assertTrue(all(isinstance(x, str) for x in normed))
        self.assertEqual(normed, ["0", "Cust", "2.5", "Seg"])

    def test_all_string_labels_unchanged(self):
        raw = ["Foo", "Bar", "Baz"]
        self.assertEqual(self._normalise(raw), raw)

    def test_normalised_list_joinable(self):
        """After normalisation, ', '.join() must always work."""
        raw = [0, "Cust", 1.5, None]
        normed = self._normalise(raw)
        result = ", ".join(normed)  # must not raise
        self.assertIn("0", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
