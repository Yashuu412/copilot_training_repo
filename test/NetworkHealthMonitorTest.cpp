// Unit tests for NetworkHealthMonitor.
// Covers TC-001..TC-010 from Doczzz/SWDD.md §7.
//
// TC-009 (saturation at UINT32_MAX) requires access to the private
// failureCount_ field. Add the following friend declaration inside
// NetworkHealthMonitor for TC-009 to compile:
//
//   friend struct NetworkHealthMonitorTestAccess;
//
// The helper struct is defined below.

#include "NetworkHealthMonitor.hpp"
#include "ILogger.hpp"
#include "MockLogger.hpp"

#include <gtest/gtest.h>

#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr const char *kLostMessage = "Communication Lost";
constexpr const char *kRestoredMessage = "Communication Restored";

// Test-only accessor. Requires `friend struct NetworkHealthMonitorTestAccess;`
// inside NetworkHealthMonitor.
struct NetworkHealthMonitorTestAccess {
    static void SetFailureCount(NetworkHealthMonitor &m, std::uint32_t value) {
        m.failureCount_ = value;
    }
};

} // namespace

// ---------------------------------------------------------------------------
// TC-001 / FR-001 — construction defaults
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR001_Construction_SetsUnknownNotAvailableAndZeroCount) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::UNKNOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::NOT_AVAILABLE);
    EXPECT_EQ(monitor.GetFailureCount(), 0U);
    EXPECT_TRUE(logger.infoMessages_.empty());
    EXPECT_TRUE(logger.errorMessages_.empty());
}

// ---------------------------------------------------------------------------
// TC-002 / FR-002 — first UP update becomes HEALTHY
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR002_FirstUp_SetsHealthy) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::HEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 0U);
    EXPECT_EQ(logger.InfoCount(kLostMessage), 0U);
    EXPECT_EQ(logger.InfoCount(kRestoredMessage), 0U);
}

// ---------------------------------------------------------------------------
// TC-003 / FR-003 — UP → DOWN increments and logs "Communication Lost"
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR003_UpToDown_IncrementsFailureCountAndLogsLost) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::DOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::UNHEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 1U);
    EXPECT_EQ(logger.InfoCount(kLostMessage), 1U);
}

// ---------------------------------------------------------------------------
// TC-004 / FR-004 — repeated DOWN does not increment
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR004_RepeatedDown_DoesNotIncrementCounterOrLogAgain) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::DOWN);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::DOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::UNHEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 1U);
    EXPECT_EQ(logger.InfoCount(kLostMessage), 1U);
}

// ---------------------------------------------------------------------------
// TC-005 / FR-005 — DOWN → UP preserves counter and logs "Communication Restored"
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR005_DownToUp_PreservesCounterAndLogsRestored) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    monitor.UpdateStatus(NetworkStatus::UP);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::HEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), 1U);
    EXPECT_EQ(logger.InfoCount(kRestoredMessage), 1U);
}

// ---------------------------------------------------------------------------
// TC-006 / FR-006 — GetHealth returns latest health
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR006_GetHealth_ReturnsLatestHealth) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::NOT_AVAILABLE);

    monitor.UpdateStatus(NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::HEALTHY);

    monitor.UpdateStatus(NetworkStatus::DOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::UNHEALTHY);

    monitor.UpdateStatus(NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::HEALTHY);
}

// ---------------------------------------------------------------------------
// TC-007 / FR-007 — GetFailureCount returns exact number of UP→DOWN transitions
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR007_GetFailureCount_MatchesUpToDownTransitions) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    for (int i = 0; i < 3; ++i) {
        monitor.UpdateStatus(NetworkStatus::UP);
        monitor.UpdateStatus(NetworkStatus::DOWN);
    }

    EXPECT_EQ(monitor.GetFailureCount(), 3U);
}

// ---------------------------------------------------------------------------
// TC-008 / FR-008 — ResetFailureCount clears counter, preserves state
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR008_ResetFailureCount_ClearsCounterAndPreservesState) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    monitor.UpdateStatus(NetworkStatus::DOWN);
    ASSERT_EQ(monitor.GetFailureCount(), 1U);

    monitor.ResetFailureCount();

    EXPECT_EQ(monitor.GetFailureCount(), 0U);
    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::DOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::UNHEALTHY);
}

// ---------------------------------------------------------------------------
// TC-009 / FR-009 — counter saturates at UINT32_MAX
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR009_CounterAtMax_DoesNotWrap) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    monitor.UpdateStatus(NetworkStatus::UP);
    NetworkHealthMonitorTestAccess::SetFailureCount(monitor, UINT32_MAX);

    monitor.UpdateStatus(NetworkStatus::DOWN);

    EXPECT_EQ(monitor.GetFailureCount(), UINT32_MAX);
    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::DOWN);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::UNHEALTHY);
    EXPECT_EQ(logger.InfoCount(kLostMessage), 1U);
}

// ---------------------------------------------------------------------------
// TC-010 / FR-003, FR-005 — multiple loss/recovery cycles
// ---------------------------------------------------------------------------
TEST(NetworkHealthMonitorTest, FR003_FR005_MultipleLossRecoveryCycles_CountsAndLogsMatch) {
    MockLogger logger;
    NetworkHealthMonitor monitor(logger);

    constexpr int kCycles = 5;
    for (int i = 0; i < kCycles; ++i) {
        monitor.UpdateStatus(NetworkStatus::UP);
        monitor.UpdateStatus(NetworkStatus::DOWN);
    }
    monitor.UpdateStatus(NetworkStatus::UP);

    EXPECT_EQ(monitor.GetStatus(), NetworkStatus::UP);
    EXPECT_EQ(monitor.GetHealth(), NetworkHealth::HEALTHY);
    EXPECT_EQ(monitor.GetFailureCount(), static_cast<std::uint32_t>(kCycles));
    EXPECT_EQ(logger.InfoCount(kLostMessage), static_cast<std::size_t>(kCycles));
    EXPECT_EQ(logger.InfoCount(kRestoredMessage), static_cast<std::size_t>(kCycles));
}

// ---------------------------------------------------------------------------
// Data-driven smoke test — walks the CSV matrix in test/test_cases.csv.
// Each row: TestID,Requirement,Scenario,InputSequence,ExpectedStatus,
//           ExpectedHealth,ExpectedCount,ExpectedLostLogs,ExpectedRestoredLogs
// InputSequence is a '|'-separated sequence of UP/DOWN/RESET tokens.
// Rows whose TestID is TC-009 are skipped (require the private accessor).
// ---------------------------------------------------------------------------
namespace {

std::vector<std::string> Split(const std::string &s, char delim) {
    std::vector<std::string> out;
    std::string token;
    std::istringstream iss(s);
    while (std::getline(iss, token, delim)) {
        out.push_back(token);
    }
    return out;
}

NetworkStatus ParseStatus(const std::string &s) {
    if (s == "UP") {
        return NetworkStatus::UP;
    }
    if (s == "DOWN") {
        return NetworkStatus::DOWN;
    }
    return NetworkStatus::UNKNOWN;
}

NetworkHealth ParseHealth(const std::string &s) {
    if (s == "HEALTHY") {
        return NetworkHealth::HEALTHY;
    }
    if (s == "UNHEALTHY") {
        return NetworkHealth::UNHEALTHY;
    }
    return NetworkHealth::NOT_AVAILABLE;
}

} // namespace

TEST(NetworkHealthMonitorCsvTest, WalksTestMatrix) {
    const char *csvPath = std::getenv("NHM_TEST_CSV");
    if (csvPath == nullptr) {
        csvPath = "test/test_cases.csv";
    }

    std::ifstream in(csvPath);
    ASSERT_TRUE(in.good()) << "cannot open " << csvPath;

    std::string line;
    std::getline(in, line); // header

    while (std::getline(in, line)) {
        if (line.empty() || line.front() == '#') {
            continue;
        }
        const auto cols = Split(line, ',');
        ASSERT_GE(cols.size(), 9U) << "malformed row: " << line;

        const std::string &testId = cols[0];
        if (testId == "TC-009") {
            continue;
        } // requires private accessor

        MockLogger logger;
        NetworkHealthMonitor monitor(logger);

        for (const auto &token : Split(cols[3], '|')) {
            if (token == "UP") {
                monitor.UpdateStatus(NetworkStatus::UP);
            } else if (token == "DOWN") {
                monitor.UpdateStatus(NetworkStatus::DOWN);
            } else if (token == "RESET") {
                monitor.ResetFailureCount();
            }
        }

        EXPECT_EQ(monitor.GetStatus(), ParseStatus(cols[4])) << testId;
        EXPECT_EQ(monitor.GetHealth(), ParseHealth(cols[5])) << testId;
        EXPECT_EQ(monitor.GetFailureCount(), static_cast<std::uint32_t>(std::stoul(cols[6])))
            << testId;
        EXPECT_EQ(logger.InfoCount(kLostMessage), static_cast<std::size_t>(std::stoul(cols[7])))
            << testId;
        EXPECT_EQ(logger.InfoCount(kRestoredMessage), static_cast<std::size_t>(std::stoul(cols[8])))
            << testId;
    }
}
