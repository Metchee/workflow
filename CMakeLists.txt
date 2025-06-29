cmake_minimum_required(VERSION 3.10)
project(Zappy)
set(CMAKE_CXX_STANDARD 17)

find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_package(PkgConfig REQUIRED)
pkg_check_modules(SFML REQUIRED sfml-graphics sfml-window sfml-system)
find_package(raylib REQUIRED)

add_subdirectory(server)
add_subdirectory(graphical)
add_subdirectory(ai)

install(TARGETS zappy_server zappy_gui DESTINATION bin)
install(PROGRAMS ${CMAKE_BINARY_DIR}/zappy_ai DESTINATION bin)
install(DIRECTORY ai/src/ DESTINATION share/zappy/ai
    FILES_MATCHING PATTERN "*.py")