/*
** EPITECH PROJECT, 2025
** zappy
** File description:
** map_parameters
*/

#ifndef MAP_PARAMETERS_H
    #define MAP_PARAMETERS_H
    #include <stdbool.h>
    #include "ressources.h"
    #define TIME_UNIT_REP 20

typedef struct server server_t;
typedef struct player_s player_t;

typedef struct map_parameters_s {
    int height;
    int width;
    int port;
    char **team_names;
    int team_size;
    int frec;
    int team_count;
} map_parameters_t;

typedef struct position_s {
    int x;
    int y;
} position_t;

typedef struct egg_s {
    int x, y;
    int team_id;
} egg_t;

typedef struct tile_s {
    ressources_t resources[7];
    int *player_ids;
    int player_count;
    int max_players;
    egg_t **eggs;
} tile_t;

typedef struct world_s {
    int width, height;
    tile_t **tiles;
} world_t;

world_t *create_map(map_parameters_t *map_data);
map_parameters_t *parse_arguments(int argc, char **argv);
bool args_error_handling(map_parameters_t *map_data);
void free_map_parameters(map_parameters_t *map_data);

int tile_add_player(tile_t *tile, int player_id);
int tile_remove_player(tile_t *tile, int player_id);
int world_update_player_position(world_t *world, int player_id,
    position_t old_pos, position_t new_pos);
player_t *world_find_player_by_id(server_t const *server, int player_id);
int *world_get_players_at_tile(world_t const *world, int x, int y, int *count);

#endif /* !MAP_PARAMETERS_H_ */
