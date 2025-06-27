/*
** EPITECH PROJECT, 2025
** Renderer
** File description:
** Renders
*/

#pragma once
#include <SFML/Graphics.hpp>
#include "GameState.hpp"
#include <array>
#include <SFML/Audio.hpp>

class Renderer {
public:
    Renderer(sf::RenderWindow& window);

    void render(const GameState& gameState);
    void setViewport(int x, int y, int width, int height);
    void playBackgroundMusic(const std::string& filepath);

private:
    sf::RenderWindow& window;
    sf::View gameView;
    sf::Font font;
    float tile_size;
    sf::Vector2f offset;
    sf::Music backgroundMusic;
    bool _musicPlaying = false;

    void renderMap(const GameState& gameState);
    void renderTile(const Tile& tile);
    void renderPlayers(const GameState& gameState);
    void renderPlayer(const Player& player);
    void renderBackground(const Tile& tile);
    void renderUI(const GameState& gameState);
    void renderResources(sf::RenderWindow& window, const Tile& tile);
    std::vector<int> computeTotalResources(const GameState& gameState);
    void drawResourceTotals(const GameState& gameState);


    sf::Color getResourceColor(const std::vector<int>& resources);
    sf::Color getTeamColor(const std::string& team_name);
    sf::Vector2f worldToScreen(int world_x, int world_y);
    void calculateTileSize(const GameState& gameState);
};
