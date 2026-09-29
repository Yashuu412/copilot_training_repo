"""Tests for validate_test_cases_csv.py.

Fixtures are defined inline as byte constants so the suite is self-contained
and has no external data-file dependencies.

Run from the repo root:

    python -m unittest .github/skills/ut-test-design/scripts/test_validate_test_cases.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_test_cases_csv as v  # noqa: E402

HEADER = (
    b"TestID,Requirement,Scenario,InputSequence,ExpectedStatus,"
    b"ExpectedHealth,ExpectedCount,ExpectedLostLogs,ExpectedRestoredLogs\n"
)

GOOD = HEADER + (
    b"TC-001,FR-001,Construction defaults,,UNKNOWN,NOT_AVAILABLE,0,0,0\n"
    b"TC-003,FR-003,UP to DOWN,UP|DOWN,DOWN,UNHEALTHY,1,1,0\n"
    b"TC-010,FR-003+FR-005,Loss/recovery cycle,UP|DOWN|UP,UP,HEALTHY,1,1,1\n"
)

# Header is missing the final column.
BAD_MISSING_COLUMN = (
    b"TestID,Requirement,Scenario,InputSequence,ExpectedStatus,"
    b"ExpectedHealth,ExpectedCount,ExpectedLostLogs\n"
    b"TC-001,FR-001,Construction defaults,,UNKNOWN,NOT_AVAILABLE,0,0\n"
)

BAD_INVALID_INPUT_TOKEN = HEADER + (
    b"TC-002,FR-002,Bad input token,SIDEWAYS,UP,HEALTHY,0,0,0\n"
)

BAD_COUNTER = HEADER + (
    b"TC-003,FR-003,Negative counter,UP|DOWN,DOWN,UNHEALTHY,-1,1,0\n"
    b"TC-004,FR-004,Overflow counter,UP|DOWN,DOWN,UNHEALTHY,4294967296,1,0\n"
)

BAD_INVALID_ENUM = HEADER + (
    b"TC-005,FR-005,Bad status token,UP,SLEEPY,HEALTHY,0,0,0\n"
    b"TC-006,FR-006,Bad health token,UP,UP,SNOOZE,0,0,0\n"
)

BAD_IDS = HEADER + (
    b"TC-007,REQ-99,Bad Requirement token,UP,UP,HEALTHY,0,0,0\n"
    b"TCX008,FR-002,Bad TestID,UP,UP,HEALTHY,0,0,0\n"
)

BAD_DUPLICATE_ID = HEADER + (
    b"TC-001,FR-001,Duplicate id,,UNKNOWN,NOT_AVAILABLE,0,0,0\n"
    b"TC-001,FR-002,Same id again,UP,UP,HEALTHY,0,0,0\n"
)

# UTF-8 BOM + CRLF endings + trailing whitespace + a blank row.
FIXABLE_WHITESPACE = (
    b"\xef\xbb\xbf"
    b"TestID,Requirement,Scenario,InputSequence,ExpectedStatus,"
    b"ExpectedHealth,ExpectedCount,ExpectedLostLogs,ExpectedRestoredLogs\r\n"
    b"TC-001,FR-001,Construction defaults ,,UNKNOWN,NOT_AVAILABLE,0,0,0 \r\n"
    b"\r\n"
    b"TC-002,FR-002,First UP,UP,UP,HEALTHY,0,0,0\r\n"
)


class ValidateGoodCsv(unittest.TestCase):
    def test_good_csv_is_clean(self) -> None:
        report, fixed = v.validate(GOOD, apply_fix=False)
        self.assertTrue(report.ok, msg=f"unexpected errors: {report.errors}")
        self.assertEqual(report.fixes, [])
        self.assertIsNone(fixed)

    def test_good_csv_is_idempotent_under_fix(self) -> None:
        report, fixed = v.validate(GOOD, apply_fix=True)
        self.assertTrue(report.ok)
        self.assertEqual(report.fixes, [])
        self.assertIsNone(fixed)


class ValidateSchemaErrors(unittest.TestCase):
    def test_missing_column_reported(self) -> None:
        report, _ = v.validate(BAD_MISSING_COLUMN, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("header mismatch" in e for e in report.errors), msg=report.errors,
        )

    def test_invalid_input_token_reported(self) -> None:
        report, _ = v.validate(BAD_INVALID_INPUT_TOKEN, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("InputSequence" in e and "SIDEWAYS" in e for e in report.errors),
            msg=report.errors,
        )

    def test_bad_counter_reported(self) -> None:
        report, _ = v.validate(BAD_COUNTER, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(any("negative" in e for e in report.errors), msg=report.errors)
        self.assertTrue(
            any("UINT32_MAX" in e for e in report.errors), msg=report.errors,
        )

    def test_invalid_enums_reported(self) -> None:
        report, _ = v.validate(BAD_INVALID_ENUM, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("ExpectedStatus" in e and "SLEEPY" in e for e in report.errors),
            msg=report.errors,
        )
        self.assertTrue(
            any("ExpectedHealth" in e and "SNOOZE" in e for e in report.errors),
            msg=report.errors,
        )

    def test_bad_ids_reported(self) -> None:
        report, _ = v.validate(BAD_IDS, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("Requirement token" in e and "REQ-99" in e for e in report.errors),
            msg=report.errors,
        )
        self.assertTrue(
            any("invalid TestID" in e and "TCX008" in e for e in report.errors),
            msg=report.errors,
        )

    def test_duplicate_id_reported(self) -> None:
        report, _ = v.validate(BAD_DUPLICATE_ID, apply_fix=False)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("duplicate TestID" in e for e in report.errors), msg=report.errors,
        )

    def test_fix_does_not_hide_schema_errors(self) -> None:
        # Auto-fix must never make a schema-invalid file appear clean.
        report, _fixed = v.validate(BAD_INVALID_ENUM, apply_fix=True)
        self.assertFalse(report.ok)


class ValidateFixableWhitespace(unittest.TestCase):
    def test_reports_fixes_without_apply(self) -> None:
        report, fixed = v.validate(FIXABLE_WHITESPACE, apply_fix=False)
        self.assertTrue(report.ok, msg=f"unexpected errors: {report.errors}")
        self.assertTrue(any("BOM" in f for f in report.fixes), msg=report.fixes)
        self.assertTrue(any("CRLF" in f for f in report.fixes), msg=report.fixes)
        self.assertTrue(any("trimmed" in f for f in report.fixes), msg=report.fixes)
        self.assertTrue(any("blank" in f for f in report.fixes), msg=report.fixes)
        self.assertIsNone(fixed)

    def test_fix_produces_clean_bytes(self) -> None:
        report, fixed = v.validate(FIXABLE_WHITESPACE, apply_fix=True)
        self.assertTrue(report.ok)
        self.assertIsNotNone(fixed)
        assert fixed is not None
        self.assertFalse(fixed.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", fixed)
        self.assertTrue(fixed.endswith(b"\n"))
        # Second pass must be a no-op (idempotent).
        report2, fixed2 = v.validate(fixed, apply_fix=True)
        self.assertTrue(report2.ok)
        self.assertEqual(report2.fixes, [])
        self.assertIsNone(fixed2)


class MainCli(unittest.TestCase):
    def _write(self, data: bytes) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="uttest-csv-"))
        dst = tmp / "test_cases.csv"
        dst.write_bytes(data)
        self.addCleanup(lambda: dst.unlink(missing_ok=True))
        return dst

    def test_exit_zero_on_good(self) -> None:
        self.assertEqual(v.main([str(self._write(GOOD))]), 0)

    def test_exit_one_on_schema_error(self) -> None:
        self.assertEqual(v.main([str(self._write(BAD_INVALID_ENUM))]), 1)

    def test_fix_flag_rewrites_file(self) -> None:
        dst = self._write(FIXABLE_WHITESPACE)
        original = dst.read_bytes()
        self.assertEqual(v.main([str(dst), "--fix"]), 0)
        after = dst.read_bytes()
        self.assertNotEqual(original, after)
        self.assertFalse(after.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", after)

    def test_missing_file_returns_two(self) -> None:
        missing = Path(tempfile.gettempdir()) / "uttest-does-not-exist.csv"
        self.assertEqual(v.main([str(missing)]), 2)


if __name__ == "__main__":
    unittest.main()
