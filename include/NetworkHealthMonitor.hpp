#pragma once

#include "ILogger.hpp"

#include <cstdint>

enum class NetworkStatus { UNKNOWN, UP, DOWN };

enum class NetworkHealth { NOT_AVAILABLE, HEALTHY, UNHEALTHY };

/// Tracks communication health from simulated UP/DOWN updates (FR-001..FR-009).
class NetworkHealthMonitor {
  public:
    explicit NetworkHealthMonitor(ILogger &logger);

    /// Applies a status update and drives the health state machine.
    void UpdateStatus(NetworkStatus status);

    NetworkStatus GetStatus() const noexcept;
    NetworkHealth GetHealth() const noexcept;
    std::uint32_t GetFailureCount() const noexcept;

    /// Clears the failure counter without changing status or health (FR-008).
    void ResetFailureCount() noexcept;

  private:
    void HandleCommunicationLoss();
    void HandleCommunicationRecovery();

    ILogger &logger_;
    NetworkStatus status_{NetworkStatus::UNKNOWN};
    NetworkHealth health_{NetworkHealth::NOT_AVAILABLE};
    std::uint32_t failureCount_{0U};

    friend struct NetworkHealthMonitorTestAccess;
};
