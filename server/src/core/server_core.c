/*
** EPITECH PROJECT, 2025
** zappy
** File description:
** server core implementation - main server management
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>
#include <netinet/tcp.h>
#include "../include/server.h"
#include "../include/server_signal.h"
#include "../include/server_network.h"
#include "../include/message_protocol.h"
#include "../include/resource_utils.h"
#include "../include/player.h"

static double get_current_time_seconds(void)
{
    struct timeval tv;

    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

static void initialize_server_fields(server_t *server, int port)
{
    server->server_fd = -1;
    server->port = port;
    server->clients = NULL;
    server->client_count = 0;
    server->max_clients = MAX_CLIENTS;
    server->next_player_id = 1;
}

static int allocate_server_resources(server_t *server)
{
    server->poll_fds = malloc(sizeof(struct pollfd) * (MAX_CLIENTS + 2));
    if (!server->poll_fds)
        return -1;
    server->signal_context = create_signal_context();
    if (!server->signal_context) {
        free(server->poll_fds);
        return -1;
    }
    return 0;
}

server_t *server_create(int port, map_parameters_t *map_data,
    world_t *world)
{
    server_t *server = NULL;

    server = malloc(sizeof(server_t));
    if (!server)
        return NULL;
    initialize_server_fields(server, port);
    if (allocate_server_resources(server) == -1) {
        free(server);
        return NULL;
    }
    server->map_data = map_data;
    server->world = world;
    return server;
}

static void handle_resource_spawning(server_t *server,
    double *last_resource_spawn_time, double resource_spawn_interval)
{
    double current_time = 0;

    current_time = get_current_time_seconds();
    if (current_time - *last_resource_spawn_time >= resource_spawn_interval) {
        printf("Spawning resources at time %.2f\n", current_time);
        put_ressources_in_tile(server->world->tiles,
            server->world->height, server->world->width, server);
        *last_resource_spawn_time = current_time;
    }
}

static void handle_poll_events_results(server_t *server)
{
    if (server->poll_fds[0].revents & POLLIN)
        server_handle_signal(server);
    if (server->poll_fds[1].revents & POLLIN)
        server_accept_client(server);
    server_process_client_events(server);
}

bool server_handle_events(server_t *server)
{
    if (handle_poll_events(server) == -1)
        return false;
    handle_poll_events_results(server);
    return true;
}

static void execute_server_loop_iteration(server_t *server,
    double *last_resource_spawn_time, double resource_spawn_interval)
{
    setup_poll_fds(server);
    if (handle_poll_events(server) == -1)
        return;
    if (server->poll_fds[0].revents & POLLIN)
        server_handle_signal(server);
    if (server->poll_fds[1].revents & POLLIN)
        server_accept_client(server);
    server_process_client_events(server);
    handle_resource_spawning(server, last_resource_spawn_time,
        resource_spawn_interval);
    process_food_consumption(server);
    usleep(1000);
}

static void initialize_server_timing(server_t *server,
    double *last_resource_spawn_time, double *resource_spawn_interval)
{
    *last_resource_spawn_time = get_current_time_seconds();
    *resource_spawn_interval = (double)TIME_UNIT_REP / server->world->frec;
    printf("Resource respawn interval: %.2f seconds (freq=%d)\n",
        *resource_spawn_interval, server->world->frec);
}

bool server_run(server_t *server)
{
    double last_resource_spawn_time = 0;
    double resource_spawn_interval = 0;

    if (!server || server->server_fd == -1)
        return false;
    initialize_server_timing(server, &last_resource_spawn_time,
        &resource_spawn_interval);
    while (!server_should_stop(server)) {
        execute_server_loop_iteration(server, &last_resource_spawn_time,
            resource_spawn_interval);
    }
    server_shutdown_sequence(server);
    return true;
}
