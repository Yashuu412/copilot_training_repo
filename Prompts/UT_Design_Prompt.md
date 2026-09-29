# Unit Test Design Prompt — Template

> Reusable prompt template for driving GitHub Copilot (or any AI assistant) to
> design and generate GoogleTest unit tests for the **Network Communication
> Health Monitor** MVP.
>
> Fill in every `<placeholder>` before sending the prompt. Do not remove the
> **Ground rules** or **Deliverables** sections — they enforce project
> conventions from [Requirement.md](../Doczzz/Requirement.md), [SWDD.md](../Doczzz/SWDD.md), and
> [../.github/copilot-instructions.md](../.github/copilot-instructions.md).

---

## 1. Context (fill in)

| Field | Value |
|---|---|
| Component under test | `<e.g. NetworkHealthMonitor>` |
| Header(s) | `<e.g. include/NetworkHealthMonitor.hpp, include/ILogger.hpp>` |
| Implementation file | `<e.g. src/NetworkHealthMonitor.cpp>` |
| Test file to create/update | `<e.g. test/NetworkHealthMonitorTest.cpp>` |
| Test framework | GoogleTest + GoogleMock (via CMake `FetchContent`) |
| Logger double | `MockLogger` (see [../test/MockLogger.hpp](../test/MockLogger.hpp)) |
| Requirement source | [Requirement.md](../Doczzz/Requirement.md) — cite FR/NFR IDs |
| Test-case source | [../test/test_cases.csv](../test/test_cases.csv) — cite TC IDs |

---

## 2. Prompt template (copy → paste into Copilot Chat)

```text
You are contributing GoogleTest unit tests for the Network Communication
Health Monitor MVP.

Target
------
- File:            <test/NetworkHealthMonitorTest.cpp>
- Class under test: <NetworkHealthMonitor>
- Requirement IDs:  <FR-00X, FR-00Y>
- Test-case IDs:    <TC-00X, TC-00Y>

Scenario
--------
<One or two sentences describing the behavior to verify. Reference the state
transition table in Doczzz/Requirement.md §9 or SWDD.md §5 when relevant.>

Input sequence
--------------
<e.g. UP → DOWN → DOWN → UP>

Expected outcome
----------------
- GetStatus()        == <NetworkStatus::...>
- GetHealth()        == <NetworkHealth::...>
- GetFailureCount()  == <N>
- Info log contains: <"Communication Lost" | "Communication Restored" | none>
- Error log:          <none | "...">

Constraints
-----------
- Use MockLogger only. Never ConsoleLogger.
- Test name format: FR<NNN>_<ShortDescription>, e.g.
    TEST(NetworkHealthMonitorTest, FR003_UpToDown_IncrementsFailureCountAndLogsLost)
- No sleeps, threads, filesystem, network, or global state.
- One behavior per test. No shared fixtures unless justified.
- Use ::testing::Contains for log-content assertions.
- Log strings are exact: "Communication Lost", "Communication Restored".
- Failure counter saturates at UINT32_MAX (FR-009); never wraps.

Deliverable
-----------
Emit only the new/updated TEST() blocks, ready to paste into
<test/NetworkHealthMonitorTest.cpp>. Do not modify production code.
```

---

## 3. Ground rules (do not remove)

The generated tests must comply with the following, taken from
[../.github/copilot-instructions.md](../.github/copilot-instructions.md) and
[Requirement.md](../Doczzz/Requirement.md):

- **Framework**: GoogleTest / GoogleMock, fetched via CMake `FetchContent`.
- **Language**: C++17. No C++20/23 features. No compiler extensions.
- **Naming**: `TEST(NetworkHealthMonitorTest, FR<NNN>_<Description>)`.
- **Test double**: `MockLogger` from [../test/MockLogger.hpp](../test/MockLogger.hpp).
  Never instantiate `ConsoleLogger` in tests.
- **Determinism**: no sleeps, threads, timers, filesystem, or sockets.
- **Isolation**: each `TEST` constructs its own `MockLogger` and
  `NetworkHealthMonitor`. No global mutable state.
- **Log assertions**: use `EXPECT_THAT(logger.infoMessages_, ::testing::Contains(std::string("...")))`.
- **Exact log strings**: `"Communication Lost"` and `"Communication Restored"` —
  no punctuation, no prefix/suffix.
- **State machine truth table**: see [Requirement.md](../Doczzz/Requirement.md) §9 and
  [SWDD.md](../Doczzz/SWDD.md) §5. Do not invent transitions.
- **Counter**: `std::uint32_t`, saturates at `UINT32_MAX` (FR-009).
- **First update** (`UNKNOWN → UP` or `UNKNOWN → DOWN`) sets the baseline and
  emits **no** log and does **not** increment the counter.
- **Coverage**: contribute toward ≥ 80 % line coverage on
  `src/NetworkHealthMonitor.cpp` (NFR-003).

---

## 4. Deliverables checklist

Before committing generated tests, verify:

- [ ] Every `TEST` name starts with the FR ID it covers.
- [ ] Every `TEST` references a row in [../test/test_cases.csv](../test/test_cases.csv).
- [ ] `MockLogger` is the only `ILogger` implementation used.
- [ ] No `std::cout`, `std::cerr`, `sleep`, `thread`, or file I/O.
- [ ] Assertions cover: status, health, failure count, expected log(s),
      and absence of unexpected logs where relevant.
- [ ] Exact log strings are used verbatim.
- [ ] Build succeeds with `-Wall -Wextra -Wpedantic -Werror`.
- [ ] `ctest` passes locally.
- [ ] PR description lists the FR/TC IDs implemented (NFR-006).

---

## 5. Worked example (reference only)

Prompt filled in for **TC-005 / FR-005** — *DOWN → UP preserves counter and
logs Restored*:

```text
Target
------
- File:            test/NetworkHealthMonitorTest.cpp
- Class under test: NetworkHealthMonitor
- Requirement IDs:  FR-005
- Test-case IDs:    TC-005

Scenario
--------
After a UP→DOWN transition (which increments the counter to 1 and logs
"Communication Lost"), a subsequent DOWN→UP transition must restore health
to HEALTHY, preserve the counter at 1, and emit "Communication Restored".

Input sequence
--------------
UP → DOWN → UP

Expected outcome
----------------
- GetStatus()       == NetworkStatus::UP
- GetHealth()       == NetworkHealth::HEALTHY
- GetFailureCount() == 1
- Info log contains: "Communication Lost" and "Communication Restored"
- Error log:          none
```

Expected generated test:

```cpp
// TC-005 / FR-005 — DOWN → UP preserves counter and logs Restored
TEST(NetworkHealthMonitorTest, FR005_DownToUp_PreservesCounterAndLogsRestored)
{
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::UP);

    EXPECT_EQ(monitor.GetStatus(),       NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(),       NetworkHealth::HEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 1U);
    EXPECT_THAT(logger.infoMessages_,
                ::testing::Contains(std::string("Communication Lost")));
    EXPECT_THAT(logger.infoMessages_,
                ::testing::Contains(std::string("Communication Restored")));
    EXPECT_TRUE(logger.errorMessages_.empty());
}
```

---

## 6. When to extend this template

Add a new section to this file (do not fork it) when:

- A new FR/NFR is added to [Requirement.md](../Doczzz/Requirement.md).
- A new component (e.g. a future `FileLogger`) needs its own test suite.
- A new test-double is introduced (document its contract here first).

Requirement or design changes belong in their own PR — never bundle them with
test generation (see [../.github/copilot-instructions.md](../.github/copilot-instructions.md) §13).
