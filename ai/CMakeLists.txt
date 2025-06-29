cmake_minimum_required(VERSION 3.10)

set(AI_PYTHON_FILES
    src/main.py
    src/game_types.py
    src/network.py
    src/protocol.py
    src/zappy_ai.py
)

configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/src/main.py
    ${CMAKE_CURRENT_BINARY_DIR}/zappy_ai_main.py
    COPYONLY
)

file(WRITE ${CMAKE_BINARY_DIR}/zappy_ai_wrapper.sh
    "#!/bin/bash\n"
    "export PYTHONPATH=\"${CMAKE_SOURCE_DIR}/ai/src:$PYTHONPATH\"\n"
    "exec \"${Python3_EXECUTABLE}\" \"${CMAKE_SOURCE_DIR}/ai/src/main.py\" \"$@\"\n"
)

file(COPY ${CMAKE_BINARY_DIR}/zappy_ai_wrapper.sh
    DESTINATION ${CMAKE_BINARY_DIR}
    FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)

add_custom_target(zappy_ai ALL
    COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/zappy_ai_wrapper.sh ${CMAKE_BINARY_DIR}/zappy_ai
    COMMAND chmod +x ${CMAKE_BINARY_DIR}/zappy_ai
    DEPENDS ${AI_PYTHON_FILES}
    COMMENT "Creating zappy_ai executable"
)

set_property(TARGET zappy_ai PROPERTY ADDITIONAL_CLEAN_FILES
    "${CMAKE_BINARY_DIR}/zappy_ai"
) 