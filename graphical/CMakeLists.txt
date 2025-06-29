cmake_minimum_required(VERSION 3.10)

include_directories(lib)

add_executable(zappy_gui
    src/Main.cpp
    src/Client_network.cpp
    src/ZappyGUI.cpp
    src/Zappy3DRenderer.cpp
    src/ZappyAbstractGUI.cpp
    src/Window.cpp
    src/GameState.cpp
    src/Renderer.cpp
    src/GuiMediator.cpp
    src/Core.cpp
)

target_link_libraries(zappy_gui PRIVATE ${SFML_LIBRARIES} raylib)
target_include_directories(zappy_gui PRIVATE ${SFML_INCLUDE_DIRS})
target_compile_options(zappy_gui PRIVATE ${SFML_CFLAGS_OTHER})

set_target_properties(zappy_gui PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)
