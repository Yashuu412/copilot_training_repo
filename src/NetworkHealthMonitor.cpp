#include "NetworkHealthMonitor.hpp"

NetworkHealthMonitor::NetworkHealthMonitor(ILogger &logger) : logger_(logger) {}

void NetworkHealthMonitor::UpdateStatus(NetworkStatus status) {
    if (status == NetworkStatus::UP) {
        if (status_ == NetworkStatus::DOWN) {
            HandleCommunicationRecovery();
        }
        status_ = NetworkStatus::UP;
        health_ = NetworkHealth::HEALTHY;
    } else if (status == NetworkStatus::DOWN) {
        if (status_ == NetworkStatus::UP) {
            HandleCommunicationLoss();
        }
        status_ = NetworkStatus::DOWN;
        health_ = NetworkHealth::UNHEALTHY;
    }
}

NetworkStatus NetworkHealthMonitor::GetStatus() const noexcept { return status_; }

NetworkHealth NetworkHealthMonitor::GetHealth() const noexcept { return health_; }

std::uint32_t NetworkHealthMonitor::GetFailureCount() const noexcept { return failureCount_; }

void NetworkHealthMonitor::ResetFailureCount() noexcept { failureCount_ = 0U; }

void NetworkHealthMonitor::HandleCommunicationLoss() {
    if (failureCount_ != UINT32_MAX) {
        ++failureCount_;
    }
    logger_.Info("Communication Lost");
}

void NetworkHealthMonitor::HandleCommunicationRecovery() { logger_.Info("Communication Restored"); }
