# Server CMakeLists.txt
cmake_minimum_required(VERSION 3.10)

include_directories(include)

add_executable(zappy_server
    src/core/main.c
    src/core/server_core.c
    src/core/signal_handling.c
    src/core/server_shutdown.c
    src/config/args_error_handling.c
    src/config/argument_parsing.c
    src/commands/command_handlers.c
    src/commands/command_eject.c
    src/commands/command_death.c
    src/commands/command_inventory.c
    src/commands/command_look.c
    src/commands/command_move.c
    src/commands/command_take_object.c
    src/commands/command_set_object.c
    src/commands/command_elevation.c
    src/commands/elevation_actions.c
    src/commands/elevation_checks.c
    src/commands/command_connect_nbr.c
    src/commands/set_handlers.c
    src/commands/set_handlers_bis.c
    src/commands/take_handlers.c
    src/commands/take_handlers_bis.c
    src/commands/command_queue.c
    src/commands/message_processing.c
    src/commands/move_player.c
    src/commands/command_broadcast.c
    src/network/client_broadcast.c
    src/network/client_communication.c
    src/network/event_polling.c
    src/network/network_management.c
    src/utils/cleanup_utils.c
    src/utils/look_utils.c
    src/utils/player_utils.c
    src/utils/resource_utils.c
    src/utils/spatial_utils.c
    src/utils/ressources_utils.c
    src/utils/network_utils.c
    src/world/player_management.c
    src/world/spatial_management.c
    src/world/world_creation.c
    src/world/world_ressources.c
    src/world/world_ressources_three.c
    src/world/world_ressources_bis.c
    src/world/food_consumption.c
)

set_target_properties(zappy_server PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
)

target_link_libraries(zappy_server PRIVATE m)
