---
name: ut-test-design
description: "Design, generate, extend, or review GoogleTest/GoogleMock unit tests for the Network Communication Health Monitor MVP (C++17). Use when the user asks to write TEST() blocks, cover FR/TC IDs, add tests for state-machine transitions (UP/DOWN/RESET), MockLogger assertions, run a review-and-fix loop over existing tests, or validate/fix the test/test_cases.csv catalog. Produces FR-tagged TEST() blocks that cite Doczzz/Requirement.md and rows in test/test_cases.csv, and bundles a CSV validator (--fix mode) plus a self-contained validator test suite. Do NOT use for production src/ or include/ changes, refactors, requirement edits, CMake/CI changes, or non-C++ tasks."
argument-hint: "FR/TC IDs to cover (e.g. 'FR-003, FR-004' or 'TC-005'), 'review' to run the review-and-fix loop, or 'validate-csv' / 'fix-csv' to run the CSV validator"
---

# UT Test Design — Network Communication Health Monitor

A workflow skill for turning requirements (FR-xxx) and catalog rows (TC-xxx)
into GoogleTest unit tests, and for keeping [test/test_cases.csv](../../../test/test_cases.csv)
schema-clean.

## When to use

- User asks to design or generate unit tests for `NetworkHealthMonitor`.
- User wants to add coverage for an FR/NFR from
  [Doczzz/Requirement.md](../../../Doczzz/Requirement.md).
- User asks to **review existing tests and fix any review comments**
  (the review-and-fix loop below).
- User asks to validate or auto-fix
  [test/test_cases.csv](../../../test/test_cases.csv).
- User adds a new row to `test_cases.csv` and wants it checked against the
  schema before commit.
- CI needs a deterministic gate on the test catalog.

## When NOT to use

- Editing production code under `src/` or `include/`.
- Modifying `Doczzz/` (requirement/design changes go in a separate PR).
- CMake, Docker, GitHub Actions, or AWS changes.
- Any non-C++ task.

## Authoritative sources (load in this order)

1. [../../../Doczzz/Requirement.md](../../../Doczzz/Requirement.md) — FR/NFR IDs and the state-machine truth table (§9).
2. [../../../Doczzz/SWDD.md](../../../Doczzz/SWDD.md) — component design.
3. [../../../test/test_cases.csv](../../../test/test_cases.csv) — canonical TC-xxx rows.
4. [../../../test/MockLogger.hpp](../../../test/MockLogger.hpp) — the only allowed `ILogger` double.
5. [../../copilot-instructions.md](../../copilot-instructions.md) — repository coding standards.
6. [../../../Prompts/UT_Design_Prompt.md](../../../Prompts/UT_Design_Prompt.md) — fill-in prompt template and checklist.

## Constraints (project rules, non-negotiable)

- DO NOT modify production code under `src/` or `include/`.
- DO NOT edit `Doczzz/` — requirement/design changes are separate PRs.
- DO NOT add dependencies beyond GoogleTest + GoogleMock (via `FetchContent`).
- DO NOT use `ConsoleLogger`, `std::cout`, `std::cerr`, sleeps, threads,
  timers, filesystem, or sockets in tests.
- DO NOT invent transitions or log strings. Exact log text is
  `"Communication Lost"` and `"Communication Restored"`.
- DO NOT wrap the failure counter — it saturates at `UINT32_MAX` (FR-009).
- ONLY emit new/updated `TEST()` blocks (or file-scoped helpers) targeted at
  [test/NetworkHealthMonitorTest.cpp](../../../test/NetworkHealthMonitorTest.cpp).

## Procedure — Test design

1. **Clarify inputs.** Confirm the FR/TC IDs, input sequence, and expected
   outcome. Ask before generating if ambiguous.
2. **Ground the design.** Read the relevant rows of
   [../../../test/test_cases.csv](../../../test/test_cases.csv) and the
   matching FR sections of
   [../../../Doczzz/Requirement.md](../../../Doczzz/Requirement.md). Verify
   the state transition against the truth table in
   [../../../Doczzz/Requirement.md](../../../Doczzz/Requirement.md) §9.
3. **Validate the catalog** (optional but recommended when adding a row):
   run [./scripts/validate_test_cases_csv.py](./scripts/validate_test_cases_csv.py)
   against [../../../test/test_cases.csv](../../../test/test_cases.csv). If
   fixable issues are reported, run again with `--fix`.
4. **Fill the template.** Use
   [../../../Prompts/UT_Design_Prompt.md](../../../Prompts/UT_Design_Prompt.md) §2
   (Target / Scenario / Input sequence / Expected outcome / Constraints).
5. **Generate the test(s).** One `TEST()` per behavior, named
   `FR<NNN>_<ShortDescription>`. Use `MockLogger`; assert status, health,
   counter, log contents (via `::testing::Contains`), and absence of
   unexpected logs where relevant.
6. **Self-check** using the checklist in
   [../../../Prompts/UT_Design_Prompt.md](../../../Prompts/UT_Design_Prompt.md) §4.
7. **Apply the edit** to
   [../../../test/NetworkHealthMonitorTest.cpp](../../../test/NetworkHealthMonitorTest.cpp)
   (or emit the block for the user to paste, if the file is not present).

## Procedure — CSV validate / fix

1. **Validate** (read-only, exit 1 on error):

   ```powershell
   python .github/skills/ut-test-design/scripts/validate_test_cases_csv.py test/test_cases.csv
   ```

2. **Auto-fix** (writes back; safe, idempotent transforms only):

   ```powershell
   python .github/skills/ut-test-design/scripts/validate_test_cases_csv.py test/test_cases.csv --fix
   ```

   Auto-fixed: UTF-8 BOM removal, CRLF → LF normalization, trailing-whitespace
   trim per cell, missing trailing newline, empty-line removal between rows.

   Reported but **NOT** auto-fixed (schema violations require human decision):
   header mismatch, missing/extra columns, malformed `TestID`/`Requirement`,
   invalid status/health tokens, negative or overflowing counters,
   unknown `InputSequence` tokens.

3. **Verify the validator itself** (self-contained, no external fixtures):

   ```powershell
   python -m unittest .github/skills/ut-test-design/scripts/test_validate_test_cases.py
   ```

## Procedure — Review & fix loop

Use this when the user says "review the tests" or "fix any review comments".
The loop repeats **review → fix → re-check** until no auto-fixable comment
remains, then reports anything that needs a human decision.

1. **Gather context.** Read
   [../../../test/NetworkHealthMonitorTest.cpp](../../../test/NetworkHealthMonitorTest.cpp),
   [../../../test/test_cases.csv](../../../test/test_cases.csv), and the
   relevant FR sections of
   [../../../Doczzz/Requirement.md](../../../Doczzz/Requirement.md).
2. **Review.** Walk every `TEST()` and CSV row against the rubric below and
   emit a numbered list of review comments, each tagged
   `[auto-fixable]` or `[needs-decision]` with a severity.
3. **Fix.** Apply every `[auto-fixable]` comment directly in
   [../../../test/NetworkHealthMonitorTest.cpp](../../../test/NetworkHealthMonitorTest.cpp)
   (and re-run the CSV `--fix` when a row is affected). Never touch
   `src/`, `include/`, or `Doczzz/`.
4. **Re-check.** Re-read the edited file and re-run the CSV validator.
   If a fix introduced a new comment, capture it.
5. **Loop.** Repeat steps 2–4 until no `[auto-fixable]` comments remain, or a
   hard cap of **5 iterations** is reached (prevents infinite loops).
6. **Report.** List the fixes applied and any remaining `[needs-decision]`
   comments (e.g. a coverage gap that needs a new requirement interpretation).

### Review rubric (each miss becomes a review comment)

- **Naming** — every `TEST` name starts with `FR<NNN>_`.
- **Traceability** — every `TEST` maps to a TC/FR; every TC row in the CSV has
  a corresponding `TEST` (flag coverage gaps such as an unimplemented TC).
- **Test double** — `MockLogger` only; no `ConsoleLogger`, `std::cout`,
  `std::cerr`.
- **Determinism** — no sleeps, threads, timers, filesystem, or sockets.
- **Isolation** — each `TEST` builds its own `MockLogger` + `NetworkHealthMonitor`;
  no shared mutable state.
- **Assertions** — cover status, health, failure count, expected log(s), and
  absence of unexpected logs where relevant.
- **Exact log strings** — `"Communication Lost"` / `"Communication Restored"`.
- **Counter** — saturates at `UINT32_MAX` (FR-009); never asserts a wrapped value.
- **Catalog** — `test_cases.csv` passes the validator (schema-clean).

### Loop safety

- Only edit the test file (and `test_cases.csv` via the validator).
- Stop and report if a fix would require changing a requirement or production code.
- Cap at 5 iterations; if comments still remain, surface them for the user.

## Output format (test design)

Return, in this order:

1. **Design summary** — a short table listing each generated test with its
   `FR-ID`, `TC-ID`, input sequence, and expected outcome.
2. **Test code** — a single C++ fenced block containing only the new/updated
   `TEST()` blocks, ready to paste into
   [../../../test/NetworkHealthMonitorTest.cpp](../../../test/NetworkHealthMonitorTest.cpp).
   Do not include unrelated includes, namespaces, or `main()`.
3. **Checklist confirmation** — one line per bullet from
   [../../../Prompts/UT_Design_Prompt.md](../../../Prompts/UT_Design_Prompt.md) §4,
   marked ✅ or ❌ with a one-line note when ❌.
4. **CSV status** (if a new TC row was added or the catalog was touched) —
   the validator's exit code and any fixes applied.

## Bundled resources

- Scripts
  - [./scripts/validate_test_cases_csv.py](./scripts/validate_test_cases_csv.py) — validator with `--fix` mode.
  - [./scripts/test_validate_test_cases.py](./scripts/test_validate_test_cases.py) — self-contained `unittest` suite (fixtures inlined).
- Prompt template
  - [../../../Prompts/UT_Design_Prompt.md](../../../Prompts/UT_Design_Prompt.md)
