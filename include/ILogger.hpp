#pragma once

/// Logging abstraction so the monitor can be tested without real I/O (NFR-002).
class ILogger {
  public:
    virtual ~ILogger() = default;
    virtual void Info(const char *message) = 0;
    virtual void Error(const char *message) = 0;
};
