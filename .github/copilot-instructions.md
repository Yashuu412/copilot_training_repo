# GitHub Copilot Instructions — Network Communication Health Monitor

The authoritative specification is [Doczzz/Requirement.md](../Doczzz/Requirement.md). Always
consult it before adding, changing, or removing behavior, and reference the FR/NFR IDs it
defines in every pull request and unit-test name.

---

## 1. Project name

**Network Communication Health Monitor** (training MVP inspired by `rbNetComCtrl_x`).

- Repository area of inspiration: `develop/bsw/src/cariad_radarbelt/Network/rbNetComCtrl_x`
- Workspace root in this repo: `Network_req/`
- CMake executable target: `network_health_monitor`
- CMake test target: `network_health_monitor_tests`

---

## 2. Description

A standalone C++17 component that:

1. Receives simulated network status updates (`UP` / `DOWN`).
2. Tracks the current communication health (`NOT_AVAILABLE` / `HEALTHY` / `UNHEALTHY`).
3. Counts valid `UP → DOWN` transitions (communication-loss events).
4. Emits `Communication Lost` and `Communication Restored` diagnostic log entries.
5. Exposes a small CLI for manual submission of updates and inspection of state.
6. Is unit-tested with GoogleTest, built with CMake, packaged as a Docker image, and
   optionally deployed to AWS for demonstration.

**In scope:** standalone C++17 component, GoogleTest tests, CMake build, Docker packaging,
GitHub Actions CI, optional AWS demo deployment.

**Out of scope:** real CAN/Ethernet, AUTOSAR RTE, ECU hardware, functional-safety
qualification, and any modification of the production `rbNetComCtrl_x` code path.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Language | C++17 |
| Build system | CMake ≥ 3.16 |
| Test framework | GoogleTest (via CMake `FetchContent`, not a system install) |
| Coverage | `gcov` + `lcov` (or `gcovr`) — reported in CI |
| Container | Docker (Linux base image, e.g. `ubuntu:22.04` or `debian:stable-slim`) |
| CI | GitHub Actions |
| Cloud (optional demo) | AWS ECR + ECS on Fargate, authenticated via GitHub OIDC |
| Compiler | GCC ≥ 9 or Clang ≥ 10 (whichever is available in the training container) |

No third-party libraries are permitted in `src/` beyond the C++ standard library. GoogleTest
is confined to `test/`.

---

## 4. Design patterns

- **Dependency Injection** — `NetworkHealthMonitor` receives an `ILogger&` in its constructor
  so tests can substitute a `MockLogger` (NFR-002).
- **Strategy / Interface segregation** — `ILogger` is a small pure-virtual interface with only
  `Info` and `Error` methods. `ConsoleLogger` is the production implementation.
- **State machine** — `UpdateStatus()` centralizes transition logic; two private helpers
  (`HandleCommunicationLoss`, `HandleCommunicationRecovery`) keep each transition in exactly
  one place (NFR-001, no duplicated logic).
- **RAII** — resources (loggers, streams) are owned by their scope; no manual `new`/`delete`.
- **Value-type enums** — `enum class NetworkStatus` and `enum class NetworkHealth` prevent
  implicit conversions and name collisions.

Do **not** introduce Singleton, global mutable state, service locators, or observer/pub-sub
patterns — they are not required by the specification and complicate testing.

---

## 5. Language versions and libraries

- **C++17** only. No compiler-specific extensions, no C++20/23 features.
- Standard library headers used by the core: `<cstdint>`, `<string>`, and typically nothing
  else. `<iostream>` is allowed **only** in `ConsoleLogger` and `main.cpp`.
- **GoogleTest** (any recent release fetched via `FetchContent_Declare`) — test-only.
- No Boost, no Abseil, no Poco, no networking or serialization libraries.
- No AUTOSAR, RTE, CAN, or Ethernet dependencies.

Minimum `CMakeLists.txt` preamble:

```cmake
cmake_minimum_required(VERSION 3.16)
project(network_health_monitor CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
```

---

## 6. Coding standards

### Naming

- `PascalCase` for types, enums, and public methods (`NetworkHealthMonitor`, `UpdateStatus`).
- `camelCase_` with trailing underscore for private data members (`failureCount_`, `logger_`).
- `UPPER_SNAKE_CASE` for enum values (`UNKNOWN`, `HEALTHY`, `UNHEALTHY`).
- Test names encode the requirement: `TEST(NetworkHealthMonitorTest, FR003_UpToDown_IncrementsFailureCount)`.

### Style

- Format with `clang-format` (LLVM style, 4-space indent, 100-column limit is acceptable).
- Prefer default member initializers in headers over long constructor initializer lists.
- One responsibility per method; avoid duplicating transition logic.
- Public APIs get **one** single-line doc comment describing the contract. Do not restate what
  the next line does.
- Prefer `const` and `noexcept` where truthful. Getters are `const`.
- Use `std::uint32_t` (not `unsigned int`) for the failure counter.
- No raw owning pointers; no manual memory management.

### Warnings

- Build with `-Wall -Wextra -Wpedantic -Werror` on GCC/Clang.
- Treat warnings as errors in CI. Do not silence warnings with casts — fix the root cause.

### What the core `NetworkHealthMonitor` must NOT do

- No `std::cout` / `std::cerr` — route everything through `ILogger`.
- No threading, timers, sleeps, or async I/O.
- No OS-specific calls, no filesystem access, no network sockets.
- No public API beyond what the requirement doc specifies.

---

## 7. State machine rules (must not drift)

| Current → Input | New state / health | Counter | Log |
|---|---|---|---|
| `UNKNOWN` → `UP`   | `UP` / `HEALTHY`     | — | — |
| `UNKNOWN` → `DOWN` | `DOWN` / `UNHEALTHY` | — (no increment) | — |
| `UP` → `UP`        | `UP` / `HEALTHY`     | — | — |
| `UP` → `DOWN`      | `DOWN` / `UNHEALTHY` | **+1 (saturating at `UINT32_MAX`)** | `Communication Lost` |
| `DOWN` → `DOWN`    | `DOWN` / `UNHEALTHY` | — | — |
| `DOWN` → `UP`      | `UP` / `HEALTHY`     | preserved | `Communication Restored` |

Log strings must match exactly: `Communication Lost` and `Communication Restored`. Do not
emit either string on `UNKNOWN → UP/DOWN` transitions — the first update sets the baseline
and is not a loss or recovery event (see FR-001..FR-005 and §9.4 of the requirement).

---

## 8. Sample test code

Reference shape for tests in `test/NetworkHealthMonitorTest.cpp`. Every test must reference
the requirement it verifies and use `MockLogger` — never `ConsoleLogger`.

```cpp
#include "ILogger.hpp"
#include "NetworkHealthMonitor.hpp"

#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <cstdint>
#include <string>
#include <vector>

class MockLogger : public ILogger
{
public:
    void Info(const char* message) override  { infoMessages_.emplace_back(message); }
    void Error(const char* message) override { errorMessages_.emplace_back(message); }

    std::vector<std::string> infoMessages_;
    std::vector<std::string> errorMessages_;
};

// TC-001 / FR-001
TEST(NetworkHealthMonitorTest, FR001_Construction_SetsUnknownAndZeroCount)
{
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    EXPECT_EQ(monitor.GetStatus(),        NetworkStatus::UNKNOWN);
    EXPECT_EQ(monitor.GetHealth(),        NetworkHealth::NOT_AVAILABLE);
    EXPECT_EQ(monitor.GetFailureCount(),  0U);
}

// TC-003 / FR-003
TEST(NetworkHealthMonitorTest, FR003_UpToDown_IncrementsFailureCountAndLogsLost)
{
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);

    EXPECT_EQ(monitor.GetHealth(),        NetworkHealth::UNHEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(),  1U);
    EXPECT_THAT(logger.infoMessages_,
                ::testing::Contains(std::string("Communication Lost")));
}

// TC-004 / FR-004
TEST(NetworkHealthMonitorTest, FR004_RepeatedDown_DoesNotIncrementCounter)
{
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::DOWN);

    EXPECT_EQ(monitor.GetFailureCount(), 1U);
}

// TC-005 / FR-005
TEST(NetworkHealthMonitorTest, FR005_DownToUp_PreservesCounterAndLogsRestored)
{
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::UP);

    EXPECT_EQ(monitor.GetHealth(),       NetworkHealth::HEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 1U);
    EXPECT_THAT(logger.infoMessages_,
                ::testing::Contains(std::string("Communication Restored")));
}
```

Test rules:

- Framework: **GoogleTest**, pulled in via CMake `FetchContent`.
- Every test name references the requirement it covers.
- Tests use `MockLogger` — never `ConsoleLogger`.
- Target **≥ 80 %** line coverage on `src/NetworkHealthMonitor.cpp` (NFR-003).
- Tests must be deterministic and independent — no shared state, no sleeps, no network.

---

## 9. Folder structure

The workspace root is `Network_req/`. The scaffolding below is created under that root as
the MVP is built out.

```
Network_req/
├── Doczzz/
│   └── Requirement.md              # authoritative requirement document
├── .github/
│   ├── copilot-instructions.md     # this file
│   └── workflows/
│       └── ci.yml                  # build, test, coverage, docker
├── include/
│   ├── ILogger.hpp
│   └── NetworkHealthMonitor.hpp
├── src/
│   ├── NetworkHealthMonitor.cpp
│   ├── ConsoleLogger.cpp
│   └── main.cpp                    # CLI entry point
├── test/
│   ├── CMakeLists.txt
│   ├── MockLogger.hpp
│   └── NetworkHealthMonitorTest.cpp
├── CMakeLists.txt
├── Dockerfile
└── README.md
```

Rules:

- Public headers go in `include/`; implementation files go in `src/`.
- Do not put GoogleTest headers, mocks, or test doubles under `src/` or `include/`.
- `main.cpp` is CLI-only; it must not contain business logic — delegate to
  `NetworkHealthMonitor` and `ConsoleLogger`.

---

## 10. Sensitive data handling (NFR-005)

- **Never commit** AWS access keys, session tokens, Bosch credentials, or any repository
  tokens. Add `.gitignore` entries for `*.pem`, `*.key`, `.env`, and local AWS config files.
- **Never log** secrets, credentials, tokens, VINs, or personally identifiable information.
  Log messages are limited to state transitions and diagnostic strings defined in the spec.
- **CI credentials:** authenticate to AWS via **GitHub OIDC** (federated identity) or repository
  secrets accessed as `${{ secrets.NAME }}`. Do not inline credentials in workflow YAML,
  Dockerfiles, or shell scripts.
- **Docker images:** do not `ADD`/`COPY` `.git`, `.env`, or CI credential files into layers.
  Use multi-stage builds and copy only the built binary into the runtime image.
- **Secret scanning:** enable GitHub secret scanning and Dependabot on the repository.
- If a secret is accidentally committed, rotate it immediately and rewrite history — do not
  rely on a follow-up commit to hide it.

---

## 11. Build & CI

- Warnings: `-Wall -Wextra -Wpedantic -Werror` on GCC/Clang.
- CMake targets: `network_health_monitor` and `network_health_monitor_tests`.
- CI stages, in order: **configure → build → `ctest` → coverage gate (≥ 80 %) → Docker build
  → local smoke test**. Any failing stage fails the workflow.
- AWS deploy is optional and only runs on the training branch, behind OIDC-federated
  credentials. If no AWS training account is available, a successful local Docker run is
  accepted as the deployment demonstration.

---

## 12. Pull-request expectations (NFR-006)

- Reference the requirement IDs the change implements, e.g. `Implements FR-003, FR-004`.
- Include or update tests for every behavior change; test names must reference the FR.
- Keep diffs focused; do not refactor unrelated code in the same PR.
- Confirm the PR review checklist in §14 of [Doczzz/Requirement.md](../Doczzz/Requirement.md).

---

## 13. What Copilot should NOT do here

- Do not introduce dependencies on AUTOSAR, RTE, CAN, or Ethernet stacks.
- Do not add threading, timers, or async I/O to the core class.
- Do not widen the public API beyond what the requirement doc specifies.
- Do not use `std::cout` / `std::cerr` inside `NetworkHealthMonitor` — always go through `ILogger`.
- Do not wrap the failure counter around; saturate at `UINT32_MAX` (FR-009).
- Do not commit generated build artifacts (`build/`, `*.o`, `*.a`, coverage HTML) — add them to `.gitignore`.
- Do not modify anything under `Doczzz/` as part of an implementation PR; requirement changes go in their own PR.
