##
## EPITECH PROJECT, 2025
## header
## File description:
## zappy ai
##

import time
import random
from game_types import Direction, Resources, ELEVATION_REQUIREMENTS
from network import NetworkClient
from protocol import ProtocolParser

class ZappyAI:
    def __init__(self, host: str, port: int, team_name: str):
        self.network = NetworkClient(host, port, team_name)
        self.parser = ProtocolParser()
        self.level = 1
        self.inventory = Resources()
        self.is_alive = True
        self.world_size = (0, 0)
        self.last_look_result: list[list[str]] = []
        self.elevation_in_progress = False
        self.last_broadcast_time = 0

        self.stuck_counter = 0
        self.max_stuck_attempts = 5
        self.last_position_state = None
        self.consecutive_same_actions = 0

    def connect_to_server(self) -> bool:
        if not self.network.connect():
            print("AI: Failed to connect to network.")
            return False
        print("AI: Network connection established.")
        success, world_size = self.network.authenticate()
        if success:
            self.world_size = world_size
            print(f"AI: Authenticated. World size: {self.world_size}")
        else:
            print("AI: Authentication failed.")
        return success

    def update_inventory(self):
        print("AI: Requesting inventory...")
        if self.network.send_command("Inventory"):
            response = self.network.receive_line()
            if response == "dead":
                print("AI: Received 'dead' after Inventory request. AI is dead.")
                self.is_alive = False
            elif response:
                self.inventory = self.parser.parse_inventory(response)
                print(f"AI: Inventory updated: {self.inventory}")
            else:
                print("AI: No response or empty response for Inventory.")
        else:
            print("AI: Failed to send Inventory command.")
            self.is_alive = False

    def look_around(self):
        print("AI: Looking around...")
        if self.network.send_command("Look"):
            response = self.network.receive_line()
            if response == "dead":
                print("AI: Received 'dead' after Look request. AI is dead.")
                self.is_alive = False
            elif response:
                old_look_result = self.last_look_result.copy() if self.last_look_result else []
                self.last_look_result = self.parser.parse_look_result(response)
                print(f"AI: Look result: {self.last_look_result}")

                if old_look_result == self.last_look_result:
                    self.stuck_counter += 1
                    print(f"AI: Same look result, stuck counter: {self.stuck_counter}")
                else:
                    self.stuck_counter = 0
            else:
                print("AI: No response or empty response for Look.")
        else:
            print("AI: Failed to send Look command.")
            self.is_alive = False

    def move_forward(self):
        print("AI: Moving forward...")
        if self.network.send_command("Forward"):
            response = self.network.receive_line()
            if response == "ok":
                print("AI: Move forward successful.")
                return True
            elif response == "dead":
                self.is_alive = False
            print(f"AI: Move forward failed or unexpected response: {response}")
            return False
        print("AI: Failed to send Forward command.")
        self.is_alive = False
        return False

    def turn_left(self):
        print("AI: Turning left...")
        if self.network.send_command("Left"):
            response = self.network.receive_line()
            if response == "ok":
                print("AI: Turn left successful.")
                self.stuck_counter = 0
                return True
            elif response == "dead":
                self.is_alive = False
            print(f"AI: Turn left failed or unexpected response: {response}")
            return False
        print("AI: Failed to send Left command.")
        self.is_alive = False
        return False

    def turn_right(self):
        print("AI: Turning right...")
        if self.network.send_command("Right"):
            response = self.network.receive_line()
            if response == "ok":
                print("AI: Turn right successful.")
                self.stuck_counter = 0
                return True
            elif response == "dead":
                self.is_alive = False
            print(f"AI: Turn right failed or unexpected response: {response}")
            return False
        print("AI: Failed to send Right command.")
        self.is_alive = False
        return False

    def take_object(self, obj: str):
        print(f"AI: Attempting to take {obj}...")
        if self.network.send_command(f"Take {obj}"):
            response = self.network.receive_line()
            if response == "ok":
                print(f"AI: Successfully took {obj}.")
                if hasattr(self.inventory, obj.lower()):
                    current_val = getattr(self.inventory, obj.lower())
                    setattr(self.inventory, obj.lower(), current_val + 1)
                self.stuck_counter = 0
                return True
            elif response == "dead":
                self.is_alive = False
            print(f"AI: Failed to take {obj} or unexpected response: {response}")
            return False
        print(f"AI: Failed to send Take {obj} command.")
        self.is_alive = False
        return False

    def set_object(self, obj: str):
        print(f"AI: Setting down {obj}...")
        if self.network.send_command(f"Set {obj}"):
            response = self.network.receive_line()
            if response == "ok":
                print(f"AI: Successfully set down {obj}.")
                if hasattr(self.inventory, obj.lower()):
                    current_val = getattr(self.inventory, obj.lower())
                    setattr(self.inventory, obj.lower(), max(0, current_val - 1))
                return True
            elif response == "dead":
                self.is_alive = False
            print(f"AI: Set command for object '{obj}' failed or unexpected response: {response}")
            return False
        print(f"AI: Failed to send Set {obj} command.")
        self.is_alive = False
        return False

    def broadcast_text(self, text: str):
        print(f"AI: Broadcasting: {text}")
        if self.network.send_command(f"Broadcast {text}"):
            response = self.network.receive_line()
            if response == "ok":
                self.last_broadcast_time = time.time()
                return True
            elif response == "dead":
                self.is_alive = False
        return False

    def incantation(self):
        print("AI: Starting incantation...")
        if self.network.send_command("Incantation"):
            response = self.network.receive_line()
            if "Elevation underway" in response:
                print("AI: Incantation started successfully.")
                final_response = self.network.receive_line()
                if "Current level:" in final_response:
                    try:
                        new_level = int(final_response.split(":")[-1].strip())
                        self.level = new_level
                        print(f"AI: Successfully elevated to level {self.level}!")
                        return True
                    except:
                        print("AI: Could not parse new level from response.")
                return True
            elif response == "ko":
                print("AI: Incantation failed.")
                return False
            elif response == "dead":
                self.is_alive = False
            return False
        print("AI: Failed to send Incantation command.")
        self.is_alive = False
        return False

    def find_resource_in_vision(self, resource: str) -> int:
        for i, tile_objects in enumerate(self.last_look_result):
            if resource in tile_objects:
                print(f"AI: {resource} found in vision at tile index {i}.")
                return i
        return -1

    def is_stuck(self) -> bool:
        return self.stuck_counter >= self.max_stuck_attempts

    def unstuck_maneuver(self):
        print(f"AI: STUCK! Performing unstuck maneuver (stuck_counter: {self.stuck_counter})")

        actions = [self.turn_left, self.turn_right, self.move_forward]

        for _ in range(random.randint(1, 3)):
            action = random.choice(actions)
            action()
            time.sleep(0.1)

        self.stuck_counter = 0
        print("AI: Unstuck maneuver completed")

    def try_collect_resource_on_current_tile(self) -> bool:
        if not self.last_look_result or len(self.last_look_result) == 0:
            return False

        current_tile = self.last_look_result[0]

        if 'food' in current_tile:
            print("AI: Found food on current tile!")
            return self.take_object('food')

        if self.level < 8:
            required = ELEVATION_REQUIREMENTS[self.level]

            resources_needed = {
                'linemate': required.linemate - self.inventory.linemate,
                'deraumere': required.deraumere - self.inventory.deraumere,
                'sibur': required.sibur - self.inventory.sibur,
                'mendiane': required.mendiane - self.inventory.mendiane,
                'phiras': required.phiras - self.inventory.phiras,
                'thystame': required.thystame - self.inventory.thystame
            }

            for resource, needed in resources_needed.items():
                if needed > 0 and resource in current_tile:
                    print(f"AI: Found needed {resource} on current tile!")
                    return self.take_object(resource)

        return False

    def smart_navigation_strategy(self) -> bool:
        if self.try_collect_resource_on_current_tile():
            return True

        if self.is_stuck():
            self.unstuck_maneuver()
            return True

        if self.level < 8:
            required = ELEVATION_REQUIREMENTS[self.level]

            resources_to_find = []
            if self.inventory.linemate < required.linemate:
                resources_to_find.append('linemate')
            if self.inventory.deraumere < required.deraumere:
                resources_to_find.append('deraumere')
            if self.inventory.sibur < required.sibur:
                resources_to_find.append('sibur')
            if self.inventory.mendiane < required.mendiane:
                resources_to_find.append('mendiane')
            if self.inventory.phiras < required.phiras:
                resources_to_find.append('phiras')
            if self.inventory.thystame < required.thystame:
                resources_to_find.append('thystame')

            for resource in resources_to_find:
                tile_idx = self.find_resource_in_vision(resource)
                if tile_idx > 0:
                    print(f"AI: Moving towards {resource} at tile index {tile_idx}")
                    return self.move_forward()

        if self.inventory.food <= 5:
            food_tile = self.find_resource_in_vision('food')
            if food_tile > 0:
                print(f"AI: Moving towards food at tile index {food_tile}")
                return self.move_forward()

        return self.exploration_strategy()

    def exploration_strategy(self) -> bool:
        print("AI: Exploring...")

        action_weights = ['forward'] * 4 + ['left'] * 2 + ['right'] * 2
        action = random.choice(action_weights)

        if action == 'forward':
            return self.move_forward()
        elif action == 'left':
            return self.turn_left()
        else:
            return self.turn_right()

    def attempt_elevation(self) -> bool:
        if self.level >= 8:
            return True

        required = ELEVATION_REQUIREMENTS[self.level]

        if not self.has_required_resources(required):
            print("AI: Don't have required resources for elevation.")
            return False

        print(f"AI: Attempting elevation from level {self.level} to {self.level + 1}")

        self.drop_elevation_stones(required)

        success = self.incantation()
        if success:
            print(f"AI: Elevation successful! Now at level {self.level}")
        else:
            print("AI: Elevation failed")

        return success

    def has_required_resources(self, required) -> bool:
        return (self.inventory.linemate >= required.linemate and
                self.inventory.deraumere >= required.deraumere and
                self.inventory.sibur >= required.sibur and
                self.inventory.mendiane >= required.mendiane and
                self.inventory.phiras >= required.phiras and
                self.inventory.thystame >= required.thystame)

    def drop_elevation_stones(self, required):
        stones = ['linemate', 'deraumere', 'sibur', 'mendiane', 'phiras', 'thystame']
        requirements = [required.linemate, required.deraumere, required.sibur,
                       required.mendiane, required.phiras, required.thystame]

        for stone, count in zip(stones, requirements):
            current_inventory = getattr(self.inventory, stone, 0)
            for _ in range(min(count, current_inventory)):
                if self.set_object(stone):
                    setattr(self.inventory, stone, getattr(self.inventory, stone) - 1)

    def enhanced_survival_strategy(self):
        if not self.is_alive:
            return False

        self.update_inventory()
        if not self.is_alive:
            return False

        self.look_around()
        if not self.is_alive:
            return False

        print(f"AI Status - Food: {self.inventory.food}, Level: {self.level}, Alive: {self.is_alive}, Stuck: {self.stuck_counter}")

        if self.inventory.food <= 2:
            print("AI: CRITICAL food level! Desperately seeking food.")
            if self.try_collect_resource_on_current_tile():
                return True
            food_tile = self.find_resource_in_vision('food')
            if food_tile > 0:
                return self.move_forward()
            return self.exploration_strategy()

        if self.level < 8:
            required = ELEVATION_REQUIREMENTS[self.level]
            if self.has_required_resources(required):
                print("AI: Have all resources for elevation! Attempting...")
                return self.attempt_elevation()

        return self.smart_navigation_strategy()

    def run(self):
        if not self.connect_to_server():
            print("AI: Could not connect to server. Exiting.")
            return

        print(f"AI: Successfully started for team {self.network.team_name}")

        try:
            while self.is_alive:
                if not self.enhanced_survival_strategy():
                    print("AI: Strategy indicated AI should stop or is dead.")
                    break

                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nAI: Keyboard interrupt detected. Stopping AI.")
        except Exception as e:
            print(f"AI: An error occurred during run: {e}")
        finally:
            print("AI: Disconnecting...")
            self.network.disconnect()
