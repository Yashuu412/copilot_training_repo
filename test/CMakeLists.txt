include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.15.2
)
# Keep GoogleTest confined to the test tree.
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(network_health_monitor_tests
    NetworkHealthMonitorTest.cpp
)
target_include_directories(network_health_monitor_tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)
target_link_libraries(network_health_monitor_tests PRIVATE
    network_health_monitor
    GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(network_health_monitor_tests)
