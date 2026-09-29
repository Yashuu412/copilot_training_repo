#pragma once

#include "ILogger.hpp"

#include <string>
#include <vector>

class MockLogger : public ILogger
{
public:
    void Info(const char* message) override
    {
        infoMessages_.emplace_back(message == nullptr ? "" : message);
    }

    void Error(const char* message) override
    {
        errorMessages_.emplace_back(message == nullptr ? "" : message);
    }

    std::size_t InfoCount(const std::string& expected) const
    {
        std::size_t n = 0U;
        for (const auto& m : infoMessages_) { if (m == expected) { ++n; } }
        return n;
    }

    void Clear()
    {
        infoMessages_.clear();
        errorMessages_.clear();
    }

    std::vector<std::string> infoMessages_;
    std::vector<std::string> errorMessages_;
};
