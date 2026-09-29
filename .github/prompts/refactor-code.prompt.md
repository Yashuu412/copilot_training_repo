---
mode: agent
description: "Refactor C++ code in the Network Communication Health Monitor MVP without changing observable behavior. Preserves the public API, state-machine truth table, and exact log strings; keeps changes small, tested, and warning-clean."
---

# Refactor Code — Network Communication Health Monitor

Refactor the selected code (or `${input:target:the file/function to refactor}`)
to improve clarity, structure, and maintainability **without changing observable
behavior**. This is a behavior-preserving change only.

Always ground the work in [Requirement.md](../../Doczzz/Requirement.md),
[SWDD.md](../../Doczzz/SWDD.md), and
[copilot-instructions.md](../copilot-instructions.md).

## Scope

- Refactor code under `src/` and `include/` (production) or `test/` (tests).
- Keep the diff focused on the requested target. Do not refactor unrelated code
  in the same pass.
- If nothing is selected, ask which file/function to refactor before proceeding.

## Hard constraints (do not violate)

- **Behavior-preserving only.** Public API signatures, return types, and the
  state-machine truth table in [Requirement.md](../../Doczzz/Requirement.md) §9
  must stay identical.
- **Exact log strings unchanged:** `"Communication Lost"` and
  `"Communication Restored"` — verbatim, no prefix/suffix.
- **Counter semantics unchanged:** `std::uint32_t`, saturates at `UINT32_MAX`
  (FR-009), never wraps.
- **C++17 only.** No C++20/23 features, no compiler-specific extensions.
- **No new dependencies.** Core `src/` uses only the standard library;
  GoogleTest stays confined to `test/`.
- **No `std::cout` / `std::cerr`** in `NetworkHealthMonitor` — route through
  `ILogger`. No threading, timers, sleeps, filesystem, or sockets.
- **Do not edit** anything under `Doczzz/` — requirement/design changes are a
  separate PR.

## Refactoring checklist (apply what fits the target)

- Remove duplicated transition logic; keep each transition in exactly one place
  (`HandleCommunicationLoss` / `HandleCommunicationRecovery`).
- Prefer default member initializers in headers over long initializer lists.
- Add `const` / `noexcept` where truthful; getters stay `const`.
- Use `PascalCase` types/methods, `camelCase_` private members,
  `UPPER_SNAKE_CASE` enum values.
- Replace raw owning pointers with RAII; no manual `new`/`delete`.
- Keep one responsibility per method; extract only when it removes real
  duplication (avoid one-use helpers).
- Do not add comments that restate the code; keep public-API doc comments to a
  single line.

## Procedure

1. **Read** the target and its callers/tests to understand the current
   contract. Confirm what behavior must be preserved.
2. **Propose** a short plan: what will change and why, and confirm no public
   API or state-machine drift.
3. **Apply** the refactor in small, reviewable edits.
4. **Verify** the build is warning-clean with
   `-Wall -Wextra -Wpedantic -Werror` and that `ctest` still passes. Run the
   build/tests and fix any regressions before finishing.
5. **Report** a summary of what changed, confirming behavior is unchanged and
   which FR/NFR IDs the code relates to.

## Definition of done

- [ ] Public API and observable behavior are unchanged.
- [ ] State-machine truth table and exact log strings are preserved.
- [ ] Builds clean with warnings-as-errors; all existing tests pass.
- [ ] Diff is focused on the requested target only.
- [ ] No changes under `Doczzz/`; no new dependencies introduced.
