#!/usr/bin/env python3
"""Validate (and optionally auto-fix) test/test_cases.csv.

Schema is defined in ../references/csv-schema.md. Auto-fix performs only
safe, idempotent whitespace/encoding transforms; schema violations are
reported and require a human decision.

Exit codes:
    0 — file is clean (or was auto-fixed and is now clean)
    1 — schema errors remain
    2 — usage / IO error
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXPECTED_HEADER = [
    "TestID",
    "Requirement",
    "Scenario",
    "InputSequence",
    "ExpectedStatus",
    "ExpectedHealth",
    "ExpectedCount",
    "ExpectedLostLogs",
    "ExpectedRestoredLogs",
]

TESTID_RE = re.compile(r"^TC-\d{3}$")
FRID_RE = re.compile(r"^FR-\d{3}$")
INPUT_TOKEN_RE = re.compile(r"^(UP|DOWN|RESET)$")
STATUS_VALUES = {"UP", "DOWN", "UNKNOWN"}
HEALTH_VALUES = {"HEALTHY", "UNHEALTHY", "NOT_AVAILABLE"}
UINT32_MAX = 2**32 - 1
BOM = "\ufeff"


@dataclass
class Report:
    fixes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _split_csv_line(line: str) -> list[str]:
    # test_cases.csv uses no quoting today; keep the splitter simple and
    # explicit so validation stays deterministic. If quoting is ever added,
    # switch to `csv.reader` here.
    return line.split(",")


def _normalize_text(raw: bytes, report: Report) -> str:
    text = raw.decode("utf-8-sig")  # strips BOM if present
    if raw.startswith(BOM.encode("utf-8")):
        report.fixes.append("removed UTF-8 BOM")
    if "\r\n" in text:
        report.fixes.append("normalized CRLF -> LF line endings")
        text = text.replace("\r\n", "\n")
    if "\r" in text:
        report.fixes.append("normalized CR -> LF line endings")
        text = text.replace("\r", "\n")
    return text


def _trim_and_drop_blanks(text: str, report: Report) -> list[str]:
    raw_lines = text.split("\n")
    kept: list[str] = []
    dropped_blank = 0
    trimmed_cells = 0
    for line in raw_lines:
        if line == "":
            dropped_blank += 1
            continue
        cells = _split_csv_line(line)
        stripped = [c.strip() for c in cells]
        if stripped != cells:
            trimmed_cells += 1
        kept.append(",".join(stripped))
    # split on "\n" always leaves one empty trailing element for a
    # newline-terminated file; that's expected and counted above.
    if trimmed_cells:
        report.fixes.append(f"trimmed whitespace in {trimmed_cells} row(s)")
    if dropped_blank > 1:
        # 1 blank is the expected trailing newline; more means real blank rows.
        report.fixes.append(f"removed {dropped_blank - 1} blank row(s)")
    elif dropped_blank == 0:
        report.fixes.append("added missing trailing newline")
    return kept


def _validate_header(header: list[str], report: Report) -> None:
    if header != EXPECTED_HEADER:
        report.errors.append(
            f"header mismatch: expected {EXPECTED_HEADER}, got {header}"
        )


def _validate_int(value: str, field_name: str, row_id: str, report: Report,
                  max_value: int = UINT32_MAX) -> None:
    try:
        n = int(value)
    except ValueError:
        report.errors.append(f"{row_id}: {field_name} is not an integer: {value!r}")
        return
    if n < 0:
        report.errors.append(f"{row_id}: {field_name} is negative: {n}")
    if n > max_value:
        report.errors.append(
            f"{row_id}: {field_name}={n} exceeds UINT32_MAX ({max_value})"
        )


def _validate_row(row: list[str], line_no: int, report: Report) -> None:
    if len(row) != len(EXPECTED_HEADER):
        report.errors.append(
            f"line {line_no}: expected {len(EXPECTED_HEADER)} columns, got {len(row)}"
        )
        return
    (test_id, requirement, _scenario, input_seq,
     status, health, count, lost, restored) = row
    row_id = test_id or f"line {line_no}"

    if not TESTID_RE.match(test_id):
        report.errors.append(f"{row_id}: invalid TestID {test_id!r} (expected TC-NNN)")

    # Requirement is a list separated by comma or '+', each token FR-NNN.
    tokens = [t.strip() for t in re.split(r"[,+]", requirement) if t.strip()]
    if not tokens:
        report.errors.append(f"{row_id}: Requirement is empty")
    for tok in tokens:
        if not FRID_RE.match(tok):
            report.errors.append(f"{row_id}: invalid Requirement token {tok!r}")

    if input_seq:
        for tok in input_seq.split("|"):
            if not INPUT_TOKEN_RE.match(tok):
                report.errors.append(
                    f"{row_id}: invalid InputSequence token {tok!r} "
                    f"(allowed: UP|DOWN|RESET)"
                )

    if status not in STATUS_VALUES:
        report.errors.append(
            f"{row_id}: invalid ExpectedStatus {status!r} (allowed: {sorted(STATUS_VALUES)})"
        )
    if health not in HEALTH_VALUES:
        report.errors.append(
            f"{row_id}: invalid ExpectedHealth {health!r} (allowed: {sorted(HEALTH_VALUES)})"
        )
    _validate_int(count, "ExpectedCount", row_id, report)
    _validate_int(lost, "ExpectedLostLogs", row_id, report)
    _validate_int(restored, "ExpectedRestoredLogs", row_id, report)


def validate(raw: bytes, apply_fix: bool = False) -> tuple[Report, bytes | None]:
    """Validate CSV bytes.

    Returns (report, fixed_bytes_or_None). `fixed_bytes` is only set when
    `apply_fix` is True AND at least one auto-fix ran.
    """
    report = Report()
    text = _normalize_text(raw, report)
    lines = _trim_and_drop_blanks(text, report)

    if not lines:
        report.errors.append("file is empty")
        return report, None

    header = _split_csv_line(lines[0])
    _validate_header(header, report)

    seen_ids: set[str] = set()
    for offset, line in enumerate(lines[1:], start=2):
        row = _split_csv_line(line)
        _validate_row(row, offset, report)
        if row and row[0]:
            if row[0] in seen_ids:
                report.errors.append(f"duplicate TestID {row[0]!r}")
            seen_ids.add(row[0])

    fixed_bytes: bytes | None = None
    if apply_fix and report.fixes:
        fixed_bytes = ("\n".join(lines) + "\n").encode("utf-8")
    return report, fixed_bytes


def _print_report(path: Path, report: Report) -> None:
    if report.fixes:
        print(f"[fix] {path}:")
        for f in report.fixes:
            print(f"  - {f}")
    if report.errors:
        print(f"[error] {path}:")
        for e in report.errors:
            print(f"  - {e}")
    if not report.fixes and not report.errors:
        print(f"[ok] {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="Path to test_cases.csv")
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply safe auto-fixes in place (whitespace/encoding only).",
    )
    args = parser.parse_args(argv)

    if not args.csv_path.is_file():
        print(f"[error] not a file: {args.csv_path}", file=sys.stderr)
        return 2

    raw = args.csv_path.read_bytes()
    report, fixed_bytes = validate(raw, apply_fix=args.fix)

    if args.fix and fixed_bytes is not None:
        args.csv_path.write_bytes(fixed_bytes)
        # Re-validate the written file so exit status reflects reality.
        report2, _ = validate(fixed_bytes, apply_fix=False)
        _print_report(args.csv_path, report)
        return 0 if report2.ok else 1

    _print_report(args.csv_path, report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
