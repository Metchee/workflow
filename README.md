# Zappy AI Client - Usage Guide

This guide explains how to compile and run the AI client for the Zappy project.

## 📋 Prerequisites

*   Python 3.x
*   The Zappy server binary (`zappy_server`) must be running and accessible.
*   (Optional) The Zappy GUI binary (`zappy_gui` or `zappy_gui.AppImage`) connected to the server.

## ⚙️ Compiling the AI

The AI comes with a `Makefile` to facilitate its compilation (creation of an executable script).

1.  **Open a terminal and navigate to the AI's source directory:**
    ```bash
    cd /path/to/your/project/ai/src/
    ```
    *Replace `/path/to/your/project/` with the actual path to your project.*

2.  **Run the `make` command:**
    ```bash
    make
    ```
    This will create an executable file named `zappy_ai` in the `ai/src/` directory.

## 🚀 Running the AI

Once the AI is compiled and the Zappy server is running:

1.  **Ensure you are in the `ai/src/` directory in your terminal.**

2.  **Execute the AI client with the appropriate options:**
    ```bash
    ./zappy_ai -p <SERVER_PORT> -n <TEAM_NAME> -m <SERVER_HOST>
    ```

    **Options:**
    *   `-p <SERVER_PORT>`: The port number the Zappy server is listening on (e.g., `4242`).
    *   `-n <TEAM_NAME>`: The name of the team the AI should join. This name must be one of those configured when starting the server (e.g., `TeamA`).
    *   `-m <SERVER_HOST>`: The IP address or hostname of the Zappy server (usually `localhost` if the server is running on your machine).

    **Example command:**
    ```bash
    ./zappy_ai -p 4242 -n TeamA -m localhost
    ```

3.  **Observe the AI:**
    *   The console where you launched the AI will display log messages about its actions.
    *   If you are using the Zappy GUI, you should see the AI's player appear and interact with the game world.

## 💡 Quick Troubleshooting

*   **If `./zappy_ai` is not found:** Ensure you have run `make` in `ai/src/` and that you are currently in that directory.
*   **AI fails to connect:**
    *   Verify that the Zappy server is running.
    *   Ensure the port (`-p`) and host (`-m`) are correct.
    *   Check that the team name (`-n`) is valid and that there are available slots for that team on the server.

---
This guide should get you started quickly with the AI. For more detailed information on the server or GUI, please refer to their respective documentation.