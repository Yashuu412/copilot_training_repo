cmake_minimum_required(VERSION 3.16)
project(network_health_monitor CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Core library (standard-library only, no third-party deps).
add_library(network_health_monitor STATIC
    src/NetworkHealthMonitor.cpp
)
target_include_directories(network_health_monitor PUBLIC include)

enable_testing()
add_subdirectory(test)
