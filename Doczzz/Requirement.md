# GitHub Copilot MVP Use Case Requirement

## Network Communication Health Monitor

**Repository area:** `develop/bsw/src/cariad_radarbelt/Network/rbNetComCtrl_x`  
**Target audience:** Automotive software development team  
**Training duration:** 16 hours, including concepts and hands-on exercises  
**Purpose:** Learn how to use GitHub Copilot across requirement analysis, design, development, unit testing, refactoring, review, CI/CD, and a simple AWS deployment.

---

## 1. Background

The Radar ECU communicates with other vehicle systems through network interfaces. A communication channel can become unavailable because of initialization failure, communication loss, or network recovery events.

For this training MVP, participants shall develop a standalone **Network Communication Health Monitor** inspired by the responsibilities of `rbNetComCtrl_x`.

The MVP shall accept simulated network status updates, maintain the current communication health, count communication failures, and provide diagnostic log messages. The implementation shall remain independent of production ECU hardware, AUTOSAR RTE, and confidential production interfaces.

---

## 2. Objective

The development team shall create a small C++ application that:

1. Receives network status updates.
2. Identifies communication loss and recovery.
3. Maintains the current health state.
4. Counts valid communication-loss events.
5. Provides APIs to read health and failure count.
6. Supports unit testing with GoogleTest.
7. Is built and tested through GitHub Actions.
8. Is packaged as a container and deployed to AWS for demonstration.

---

## 3. Training Scope

### 3.1 Included

- Requirement analysis and acceptance criteria
- Simple component and interface design
- C++ implementation with GitHub Copilot assistance
- Unit-test generation and execution
- Refactoring and code-quality improvement
- Pull-request review
- GitHub Actions build and test workflow
- Docker packaging
- Demonstration deployment to AWS

### 3.2 Excluded

- Production modification of `rbNetComCtrl_x`
- AUTOSAR RTE integration
- Real CAN or Ethernet hardware access
- Vehicle-level network management
- Functional-safety qualification
- Production AWS architecture
- Production security assessment
- ECU flashing or vehicle deployment
- Performance benchmarking on target hardware

---

## 4. Stakeholders

| Role | Responsibility |
|---|---|
| Product Owner or Trainer | Clarifies requirements and accepts the MVP |
| Developer | Designs, implements, tests, and refactors the component |
| Reviewer | Reviews requirements, code, tests, and workflow changes |
| DevOps Participant | Creates the CI/CD pipeline and AWS demo deployment |

---

## 5. User Story

**As a network software developer, I want to monitor simulated communication status so that I can identify communication loss, track failure occurrences, and confirm recovery through a simple API and logs.**

---

## 6. Assumptions

- The solution uses C++17 or the version already supported by the selected training environment.
- Network input is simulated as `UP` or `DOWN`.
- The initial communication status is `UNKNOWN` until the first update is received.
- A failure is counted only when the state transitions from `UP` to `DOWN`.
- Repeated `DOWN` updates shall not increment the counter.
- The training application runs on a developer machine and in a Linux container.
- AWS deployment is only a learning demonstration and does not represent ECU deployment.

---

## 7. Functional Requirements

### FR-001: Initialize the Monitor

The component shall initialize with:

- Network status set to `UNKNOWN`.
- Network health set to `NOT_AVAILABLE`.
- Failure count set to `0`.

#### Acceptance Criteria

```gherkin
Given a new NetworkHealthMonitor instance
When no status update has been received
Then the network status shall be UNKNOWN
And the network health shall be NOT_AVAILABLE
And the failure count shall be 0
```

---

### FR-002: Process an Available Network

When an `UP` status is received, the component shall set the health state to `HEALTHY`.

#### Acceptance Criteria

```gherkin
Given the monitor is initialized or the previous status is DOWN
When an UP status is received
Then the current status shall be UP
And the network health shall be HEALTHY
```

---

### FR-003: Detect Communication Loss

When the status changes from `UP` to `DOWN`, the component shall:

- Set the health state to `UNHEALTHY`.
- Increment the failure count by one.
- Create a `Communication Lost` log entry.

#### Acceptance Criteria

```gherkin
Given the current network status is UP
When a DOWN status is received
Then the current status shall be DOWN
And the network health shall be UNHEALTHY
And the failure count shall increase by 1
And a Communication Lost log shall be generated
```

---

### FR-004: Ignore Repeated Failure Updates

Repeated `DOWN` updates without an intermediate `UP` update shall not increase the failure count.

#### Acceptance Criteria

```gherkin
Given the current network status is DOWN
And the current failure count is 1
When another DOWN status is received
Then the network health shall remain UNHEALTHY
And the failure count shall remain 1
And no additional Communication Lost transition log shall be generated
```

---

### FR-005: Detect Communication Recovery

When the status changes from `DOWN` to `UP`, the component shall:

- Set the health state to `HEALTHY`.
- Preserve the existing failure count.
- Create a `Communication Restored` log entry.

#### Acceptance Criteria

```gherkin
Given the current network status is DOWN
And the failure count is greater than 0
When an UP status is received
Then the current status shall be UP
And the network health shall be HEALTHY
And the failure count shall remain unchanged
And a Communication Restored log shall be generated
```

---

### FR-006: Provide Health Status

The component shall provide an API to retrieve the current network health.

```cpp
NetworkHealth GetHealth() const;
```

Possible return values:

- `NOT_AVAILABLE`
- `HEALTHY`
- `UNHEALTHY`

#### Acceptance Criteria

```gherkin
Given the monitor has processed a status update
When GetHealth is called
Then the API shall return the health corresponding to the latest valid status
```

---

### FR-007: Provide Failure Count

The component shall provide an API to retrieve the accumulated failure count.

```cpp
std::uint32_t GetFailureCount() const;
```

#### Acceptance Criteria

```gherkin
Given one or more UP to DOWN transitions have occurred
When GetFailureCount is called
Then the API shall return the number of UP to DOWN transitions
```

---

### FR-008: Reset Failure Count

The component shall provide an API to reset the failure count without changing the current network status or health.

```cpp
void ResetFailureCount();
```

#### Acceptance Criteria

```gherkin
Given the failure count is greater than 0
When ResetFailureCount is called
Then the failure count shall become 0
And the current status shall remain unchanged
And the current health shall remain unchanged
```

---

### FR-009: Prevent Counter Overflow

If the failure count reaches `UINT32_MAX`, additional communication-loss transitions shall not wrap the counter to zero.

#### Acceptance Criteria

```gherkin
Given the failure count is UINT32_MAX
When another UP to DOWN transition occurs
Then the failure count shall remain UINT32_MAX
And the component shall remain operational
```

---

### FR-010: Provide a Demonstration Interface

The training application shall provide a small command-line interface or HTTP endpoint that allows a user to:

- Submit `UP` or `DOWN`.
- Read the current status.
- Read the current health.
- Read the failure count.
- Reset the failure count.

A command-line interface is the minimum acceptable implementation. An HTTP interface is optional and may be used for the AWS demonstration.

---

## 8. Non-Functional Requirements

### NFR-001: Maintainability

- Production code shall use clear names and single-purpose methods.
- Public APIs shall include concise documentation.
- Duplicate transition logic shall be avoided.

### NFR-002: Testability

- Network status processing shall not depend on physical CAN or Ethernet hardware.
- Logging shall be replaceable or mockable in unit tests.

### NFR-003: Code Quality

- The project shall compile without compiler errors.
- Enabled compiler warnings shall be reviewed.
- All automated unit tests shall pass.
- Line coverage for the new monitor component shall be at least 80%.

### NFR-004: Portability

- The MVP shall compile in a Linux-based training environment.
- The component shall avoid operating-system-specific logic unless isolated behind an interface.

### NFR-005: Security

- No Bosch credentials, repository tokens, AWS keys, or confidential data shall be committed.
- GitHub Actions shall obtain AWS credentials through approved repository secrets or federated identity.
- Logs shall not contain secrets or personally identifiable information.

### NFR-006: Traceability

- Each implementation pull request shall reference the corresponding requirement IDs.
- Unit-test names shall identify the behavior or requirement being verified.

---

## 9. Proposed Design

### 9.1 Enumerations

```cpp
#include <cstdint>

enum class NetworkStatus
{
    UNKNOWN,
    UP,
    DOWN
};

enum class NetworkHealth
{
    NOT_AVAILABLE,
    HEALTHY,
    UNHEALTHY
};
```

### 9.2 Logger Interface

```cpp
class ILogger
{
public:
    virtual ~ILogger() = default;
    virtual void Info(const char* message) = 0;
    virtual void Error(const char* message) = 0;
};
```

### 9.3 Monitor Interface

```cpp
class NetworkHealthMonitor
{
public:
    explicit NetworkHealthMonitor(ILogger& logger);

    void UpdateStatus(NetworkStatus status);
    NetworkStatus GetStatus() const;
    NetworkHealth GetHealth() const;
    std::uint32_t GetFailureCount() const;
    void ResetFailureCount();

private:
    void HandleCommunicationLoss();
    void HandleCommunicationRecovery();

    ILogger& logger_;
    NetworkStatus status_{NetworkStatus::UNKNOWN};
    NetworkHealth health_{NetworkHealth::NOT_AVAILABLE};
    std::uint32_t failureCount_{0U};
};
```

### 9.4 State Transitions

| Current Status | Input | New Status | Health | Counter Action | Log |
|---|---|---|---|---|---|
| `UNKNOWN` | `UP` | `UP` | `HEALTHY` | None | Optional initialization log |
| `UNKNOWN` | `DOWN` | `DOWN` | `UNHEALTHY` | None | Optional initialization log |
| `UP` | `UP` | `UP` | `HEALTHY` | None | None |
| `UP` | `DOWN` | `DOWN` | `UNHEALTHY` | Increment | Communication Lost |
| `DOWN` | `DOWN` | `DOWN` | `UNHEALTHY` | None | None |
| `DOWN` | `UP` | `UP` | `HEALTHY` | Preserve | Communication Restored |

> Training decision: The first `UNKNOWN` to `DOWN` update does not increment the failure counter because no previously healthy communication was observed.

---

## 10. Suggested Project Structure

```text
network-health-monitor/
├── CMakeLists.txt
├── Dockerfile
├── README.md
├── include/
│   ├── ILogger.hpp
│   └── NetworkHealthMonitor.hpp
├── src/
│   ├── NetworkHealthMonitor.cpp
│   └── main.cpp
├── test/
│   └── NetworkHealthMonitorTest.cpp
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 11. Minimum Unit-Test Set

| Test ID | Scenario | Expected Result | Requirement |
|---|---|---|---|
| TC-001 | Create monitor | `UNKNOWN`, `NOT_AVAILABLE`, count `0` | FR-001 |
| TC-002 | Receive first `UP` | Health becomes `HEALTHY` | FR-002 |
| TC-003 | Transition `UP` to `DOWN` | Health becomes `UNHEALTHY`, count increments | FR-003 |
| TC-004 | Receive repeated `DOWN` | Count does not increment again | FR-004 |
| TC-005 | Transition `DOWN` to `UP` | Health becomes `HEALTHY`, recovery logged | FR-005 |
| TC-006 | Query health | Latest health is returned | FR-006 |
| TC-007 | Query failure count | Correct transition count is returned | FR-007 |
| TC-008 | Reset failure count | Count becomes `0`; state is unchanged | FR-008 |
| TC-009 | Counter at `UINT32_MAX` | Counter does not wrap | FR-009 |
| TC-010 | Multiple loss and recovery cycles | Count equals number of `UP` to `DOWN` transitions | FR-003, FR-005 |

---

## 12. GitHub Copilot Learning Activities

Participants may use GitHub Copilot to:

1. Convert the user story into functional requirements and acceptance criteria.
2. Identify ambiguity in initial state, repeated events, and counter overflow.
3. Generate the class skeleton from the proposed interfaces.
4. Implement state-transition logic.
5. Generate GoogleTest test cases from acceptance criteria.
6. Explain failed tests and compiler warnings.
7. Suggest refactoring for readability and testability.
8. Review a pull-request diff for defects, missing tests, and unclear naming.
9. Generate and explain a GitHub Actions workflow.
10. Generate a Dockerfile and deployment documentation.

All Copilot-generated output shall be reviewed by a developer before it is accepted.

---

## 13. CI/CD Requirements

### 13.1 Continuous Integration

The GitHub Actions workflow shall run on pull requests and pushes to the training branch.

The workflow shall include:

1. Checkout source code.
2. Configure the CMake project.
3. Build the application and tests.
4. Run unit tests.
5. Generate a coverage report.
6. Fail the workflow if build or tests fail.
7. Build the Docker image after quality checks pass.

### 13.2 Continuous Deployment

For the training demonstration, the pipeline shall:

1. Authenticate to AWS without storing credentials in source code.
2. Push the Docker image to Amazon Elastic Container Registry.
3. Deploy or update the container on the selected AWS training runtime.
4. Execute a simple smoke test.

The AWS deployment may be implemented with Amazon ECS on AWS Fargate or another trainer-approved sandbox service. The AWS stage is not applicable when the organization does not provide a training AWS account; in that case, a successful local Docker run shall be accepted as the deployment demonstration.

### 13.3 Smoke Test

The smoke test shall confirm that:

- The process starts successfully.
- A status update can be submitted.
- The reported health matches the submitted status.
- The failure count can be queried.

---

## 14. Pull-Request Review Checklist

- [ ] Implementation matches FR-001 through FR-010.
- [ ] Boundary cases are covered.
- [ ] Repeated `DOWN` updates do not inflate the counter.
- [ ] Counter overflow is handled.
- [ ] Public APIs are understandable.
- [ ] No production repository behavior is unintentionally modified.
- [ ] Unit tests are deterministic and independent.
- [ ] New-component line coverage is at least 80%.
- [ ] No credentials or confidential data are committed.
- [ ] GitHub Actions build and tests pass.
- [ ] Docker image starts successfully.
- [ ] Requirement IDs are referenced in the pull request.

---

## 15. Definition of Done

The MVP is complete when:

- [ ] Requirements and assumptions are reviewed.
- [ ] Design interfaces and state transitions are documented.
- [ ] The C++ component is implemented.
- [ ] The minimum unit-test set passes.
- [ ] New-component line coverage is at least 80%.
- [ ] Refactoring is completed without changing expected behavior.
- [ ] Pull-request review findings are resolved.
- [ ] GitHub Actions completes successfully.
- [ ] The Docker image is created.
- [ ] AWS or approved local-container deployment succeeds.
- [ ] The smoke test passes.
- [ ] No credentials or confidential information are present in code or logs.

---

## 16. Training Plan: 16 Hours

| Stage | Concept | Hands-on | Total |
|---|---:|---:|---:|
| Requirement analysis and Copilot prompting | 1.0 h | 1.0 h | 2.0 h |
| Design and interface definition | 0.5 h | 1.0 h | 1.5 h |
| C++ development | 1.0 h | 2.5 h | 3.5 h |
| Unit testing and coverage | 0.5 h | 2.0 h | 2.5 h |
| Refactoring | 0.5 h | 0.5 h | 1.0 h |
| Pull-request review | 0.5 h | 0.5 h | 1.0 h |
| GitHub Actions CI/CD | 0.5 h | 1.5 h | 2.0 h |
| Docker and AWS deployment demonstration | 0.5 h | 1.5 h | 2.0 h |
| Retrospective and final verification | 0.25 h | 0.25 h | 0.5 h |
| **Total** | **5.25 h** | **10.75 h** | **16.0 h** |

---

## 17. Deliverables

1. Approved Markdown requirement document.
2. C++ header and source files.
3. GoogleTest unit tests.
4. CMake build configuration.
5. GitHub Actions workflow.
6. Coverage report.
7. Dockerfile.
8. AWS or local-container deployment evidence.
9. Pull-request review record.
10. Short demonstration of status loss, recovery, and failure-count behavior.

---

## 18. Requirement Traceability Matrix

| Requirement | Design Element | Verification |
|---|---|---|
| FR-001 | Constructor and default members | TC-001 |
| FR-002 | `UpdateStatus()` | TC-002 |
| FR-003 | `HandleCommunicationLoss()` | TC-003, TC-010 |
| FR-004 | Transition guard in `UpdateStatus()` | TC-004 |
| FR-005 | `HandleCommunicationRecovery()` | TC-005, TC-010 |
| FR-006 | `GetHealth()` | TC-006 |
| FR-007 | `GetFailureCount()` | TC-007 |
| FR-008 | `ResetFailureCount()` | TC-008 |
| FR-009 | Saturating increment | TC-009 |
| FR-010 | CLI or optional HTTP adapter | Smoke test |
| NFR-001 | Naming, structure, documentation | Pull-request review |
| NFR-002 | Dependency injection for logger | Unit-test review |
| NFR-003 | Build, tests, and coverage | CI workflow |
| NFR-004 | CMake and Linux container | CI and deployment |
| NFR-005 | Secrets handling and log review | Pipeline and PR review |
| NFR-006 | Requirement IDs in tests and PR | Traceability review |

---

## 19. Completion Criteria for the Training

A participant successfully completes the use case by demonstrating:

- Requirement-to-code traceability.
- Correct handling of communication loss and recovery.
- Automated tests for normal, repeated, and boundary behavior.
- A reviewed and refactored implementation.
- A green CI workflow.
- A running container in AWS or the approved local fallback.
- Clear explanation of which outputs were generated by Copilot and how they were technically verified.
