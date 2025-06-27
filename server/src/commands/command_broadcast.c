/*
** EPITECH PROJECT, 2025
** zappy
** File description:
** command_broadcast.c
*/

#include <stdio.h>
#include <string.h>
#include "server.h"
#include "player.h"
#include "command_handlers.h"
#include "server_network.h"
#include "map_parameters.h"
#include "look_direction_utils.h"
#include <math.h>
#include <stdlib.h>
#include "command_broadcast.h"

static void get_shortest_delta(server_t *server, player_t *emitter,
    player_t *receiver, delta_t *delta)
{
    int w = server->map_data->width;
    int h = server->map_data->height;

    delta->dx = emitter->x - receiver->x;
    delta->dy = emitter->y - receiver->y;
    if (delta->dx > w / 2)
        delta->dx -= w;
    if (delta->dx < - w / 2)
        delta->dx += w;
    if (delta->dy > h / 2)
        delta->dy -= h;
    if (delta->dy < - h / 2)
        delta->dy += h;
}

static int get_sector_from_angle(double angle)
{
    int sector = (int)((angle + 22.5) / 45.0);

    sector = (sector + 2) % 8;
    return sector;
}

static int get_orientation_offset(int orientation)
{
    if (orientation == 1)
        return 0;
    if (orientation == 2)
        return 2;
    if (orientation == 3)
        return 4;
    if (orientation == 4)
        return 6;
    return 0;
}

static int compute_direction(int dx, int dy, int orientation)
{
    double angle;
    int sector;
    int offset;
    int dir;

    if (dx == 0 && dy == 0)
        return 0;
    angle = atan2((double)dy, (double)dx) * 180.0 / M_PI;
    if (angle < 0)
        angle += 360.0;
    sector = get_sector_from_angle(angle);
    offset = get_orientation_offset(orientation);
    dir = ((sector + offset) % 8) + 1;
    return dir;
}

static int get_direction(server_t *server, player_t *emitter,
    player_t *receiver)
{
    delta_t delta;

    get_shortest_delta(server, emitter, receiver, &delta);
    return compute_direction(delta.dx, delta.dy, receiver->orientation);
}

static void send_broadcast_to_player(server_t *server,
    client_connection_t *from, client_connection_t *to,
    const char *msg)
{
    int dir = get_direction(server, from->client.player, to->client.player);

    server_send_to_client(to, "message %d, %s\n", dir, msg);
}

static void broadcast_to_all(server_t *server, client_connection_t *from,
    const char *msg)
{
    for (client_connection_t *curr = server->clients;
        curr; curr = curr->next) {
        if (curr->client.player && curr != from)
            send_broadcast_to_player(server, from, curr, msg);
    }
}

int handle_broadcast_cmd(server_t *server, client_connection_t *client,
    const char *command)
{
    const char *msg = command;

    if (!server || !client || !client->client.player)
        return -1;
    if (strncmp(msg, "Broadcast ", 10) == 0)
        msg += 10;
    broadcast_to_all(server, client, msg);
    server_send_to_client(client, "ok\n");
    return 0;
}
