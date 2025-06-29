/*
** EPITECH PROJECT, 2025
** zappy
** File description:
** server network setup and event handling
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

static int create_server_socket(server_t *server)
{
    int opt = 1;

    server->server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server->server_fd == -1) {
        perror("socket");
        return -1;
    }
    if (setsockopt(server->server_fd, SOL_SOCKET, SO_REUSEADDR,
        &opt, sizeof(opt)) == -1) {
        perror("setsockopt");
        close(server->server_fd);
        return -1;
    }
    if (!set_nonblocking(server->server_fd)) {
        close(server->server_fd);
        return -1;
    }
    return 0;
}

static int setup_socket_address(server_t *server, struct sockaddr_in *addr)
{
    memset(addr, 0, sizeof(*addr));
    addr->sin_family = AF_INET;
    addr->sin_addr.s_addr = INADDR_ANY;
    addr->sin_port = htons(server->port);
    if (bind(server->server_fd, (struct sockaddr *)addr,
        sizeof(*addr)) == -1) {
        perror("bind");
        close(server->server_fd);
        return -1;
    }
    return 0;
}

static int setup_socket_listen(server_t *server)
{
    int opt = 1;

    if (listen(server->server_fd, SOMAXCONN) == -1) {
        perror("listen");
        close(server->server_fd);
        return -1;
    }
    if (setsockopt(server->server_fd, IPPROTO_TCP, TCP_NODELAY,
        &opt, sizeof(opt)) == -1) {
        perror("setsockopt TCP_NODELAY");
    }
    return 0;
}

static int bind_and_listen(server_t *server)
{
    struct sockaddr_in addr;

    if (setup_socket_address(server, &addr) == -1)
        return -1;
    return setup_socket_listen(server);
}

static int setup_server_components(server_t *server)
{
    if (create_server_socket(server) == -1)
        return ERROR;
    if (bind_and_listen(server) == -1)
        return ERROR;
    if (server_setup_signals(server) == -1)
        return ERROR;
    return SUCCESS;
}

int server_start(server_t *server)
{
    if (!server)
        return ERROR;
    if (setup_server_components(server) == ERROR)
        return ERROR;
    printf("Server listening on port %d\n", server->port);
    return SUCCESS;
}

static void handle_client_event_result(server_t *server,
    client_connection_t *client)
{
    if (server_read_client_data(server, client) == -1) {
        server_disconnect_client(server, client);
    } else {
        server_process_client_commands(server, client);
    }
}

static void server_handle_client_events(server_t *server,
    client_connection_t *client)
{
    if (client) {
        handle_client_event_result(server, client);
    }
}

void server_process_client_events(server_t *server)
{
    client_connection_t *client = NULL;
    int original_client_count = 0;
    int i = 0;

    original_client_count = server->client_count;
    for (i = 2; i < original_client_count + 2; i++) {
        if (!(server->poll_fds[i].revents & POLLIN))
            continue;
        client = server_find_client_by_fd(server, server->poll_fds[i].fd);
        if (!client)
            continue;
        server_handle_client_events(server, client);
    }
}
