##
## EPITECH PROJECT, 2025
## header
## File description:
## zappy ai ultra simplifié
##

import time
import random
from game_types import Direction, Resources, ELEVATION_REQUIREMENTS, RESOURCE_NAMES
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
        
        self.action_count = 0
        self.last_inventory_check = 0
        
        self.state = "SURVIVAL"
        self.target_resource = "food"
        
        self.looking_for_partner = False
        self.partner_search_timeout = 0
        self.just_broadcasted = False
        self.broadcast_cooldown = 0
        self.is_elevation_leader = False
        self.waiting_for_incantation = False

    def connect_to_server(self) -> bool:import time
import random
from game_types import Direction, Resources, ELEVATION_REQUIREMENTS, RESOURCE_NAMES
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
        
        self.action_count = 0
        self.last_inventory_check = 0
        self.last_elevation_attempt = 0  # Cooldown pour éviter le spam d'élévation
        
        self.state = "SURVIVAL"
        self.target_resource = "food"
        
        self.looking_for_partner = False
        self.partner_search_timeout = 0
        self.just_broadcasted = False
        self.broadcast_cooldown = 0
        self.is_elevation_leader = False
        self.waiting_for_incantation = False
        self.target_tile = None
        self.leader_position = None
        self.client_id = random.randint(1, 1000)
        self.last_look_result = []

    def connect_to_server(self) -> bool:
        if not self.network.connect():
            print("AI: Failed to connect")
            return False
            
        success, world_size = self.network.authenticate()
        if success:
            self.world_size = world_size
            print(f"AI: Connected! World: {world_size}")
            return True
        else:
            print("AI: Authentication failed")
            return False

    def execute_command(self, command: str) -> str:
        if not self.network.send_command(command):
            self.is_alive = False
            return "dead"
        
        while True:
            response = self.network.receive_line()
            if response == "":
                time.sleep(0.01)
                continue
            if response == "dead":
                self.is_alive = False
            elif response.startswith("message"):
                self.handle_broadcast(response)
                continue
            print(f"AI: Command '{command}' response: {response}")
            return response

    def handle_broadcast(self, message: str):
        try:
            if ", " in message:
                parts = message.split(", ", 1)
                if len(parts) >= 2:
                    direction = int(parts[0].split()[1])
                    content = parts[1].strip()
                    
                    if direction == 0:
                        return
                    
                    if content.startswith(f"NEED_PARTNER_{self.level}_") and \
                       not self.just_broadcasted and \
                       not self.looking_for_partner and \
                       time.time() > self.broadcast_cooldown and \
                       self.state == "COLLECT" and \
                       self.has_elevation_resources():
                        _, client_id, pos_x, pos_y = content.split("_")
                        print(f"AI: Client {client_id} needs partner for level {self.level} at ({pos_x}, {pos_y})")
                        self.execute_command(f"Broadcast JOINING_{self.level}_{self.client_id}")
                        self.broadcast_cooldown = time.time() + 3
                        self.waiting_for_incantation = True
                        self.state = "MOVING_TO_LEADER"
                        self.leader_position = (int(pos_x), int(pos_y), direction)
                    
                    elif content == f"JOINING_{self.level}_{self.client_id}" and self.looking_for_partner:
                        print(f"AI: Partner found for level {self.level}! I am the leader.")
                        self.looking_for_partner = False
                        self.is_elevation_leader = True
                        self.state = "ELEVATING"
                    
                    elif content == f"LEADER_READY_{self.level}_{self.client_id}":
                        print(f"AI: Leader is ready for level {self.level} elevation")
                        self.waiting_for_incantation = True
                        self.state = "ELEVATING"
                    
                    elif content == f"STARTING_INCANTATION_{self.level}_{self.client_id}":
                        print(f"AI: Leader is starting incantation for level {self.level}")
                        self.waiting_for_incantation = True
                        self.state = "ELEVATING"
                        
        except Exception as e:
            print(f"AI: Error in broadcast: {e}")

    def update_inventory(self) -> bool:
        response = self.execute_command("Inventory")
        if response and response != "dead" and response != "ko" and response != "ok":
            self.inventory = self.parser.parse_inventory(response)
            self.last_inventory_check = time.time()
            print(f"AI: Inventory updated - Food: {self.inventory.food}, Level: {self.level}")
            return True
        print(f"AI: Inventory update failed - response: {response}")
        return False

    def look_around(self) -> list:
        response = self.execute_command("Look")
        if response and response != "dead" and response != "ko" and response != "ok":
            self.last_look_result = self.parser.parse_look_result(response)
            print(f"AI: Look result: {self.last_look_result}")
            return self.last_look_result
        print(f"AI: Look failed - response: {response}")
        return []

    def find_closest_resource(self, resource: str) -> int:
        if not self.last_look_result:
            return -1
        
        for i, tile_objects in enumerate(self.last_look_result):
            if resource in tile_objects:
                print(f"AI: Found {resource} at tile {i}")
                return i
        return -1

    def move_to_tile(self, tile_index: int) -> bool:
        if tile_index == 0:
            return True
        if tile_index <= 8:
            return self.execute_command("Forward") == "ok"
        else:
            if random.choice([True, False]):
                self.execute_command("Left")
            else:
                self.execute_command("Right")
            return self.execute_command("Forward") == "ok"

    def move_to_leader(self, direction: int) -> bool:
        if direction == 0:
            return True
        elif direction in [1, 2, 8]:
            return self.execute_command("Forward") == "ok"
        elif direction in [3, 4]:
            self.execute_command("Left")
            return self.execute_command("Forward") == "ok"
        elif direction in [5, 6, 7]:
            self.execute_command("Right")
            return self.execute_command("Forward") == "ok"
        return False

    def try_collect_resource(self, resource: str) -> bool:
        if not self.last_look_result:
            self.look_around()
        
        current_tile = self.last_look_result[0] if self.last_look_result else []
        if resource in current_tile:
            response = self.execute_command(f"Take {resource}")
            if response == "ok":
                print(f"AI: Collected {resource}")
                if hasattr(self.inventory, resource.lower()):
                    current_val = getattr(self.inventory, resource.lower())
                    setattr(self.inventory, resource.lower(), current_val + 1)
                return True
        
        tile_index = self.find_closest_resource(resource)
        if tile_index >= 0:
            return self.move_to_tile(tile_index)
        
        return self.move_randomly()

    def move_randomly(self) -> bool:
        action = random.choice(["Forward", "Left", "Right"])
        response = self.execute_command(action)
        return response == "ok"

    def needs_food_urgently(self) -> bool:
        return self.inventory.food <= 5

    def has_elevation_resources(self) -> bool:
        if self.level >= 8:
            return False
            
        req = ELEVATION_REQUIREMENTS[self.level]
        return (self.inventory.linemate >= req.linemate and
                self.inventory.deraumere >= req.deraumere and
                self.inventory.sibur >= req.sibur and
                self.inventory.mendiane >= req.mendiane and
                self.inventory.phiras >= req.phiras and
                self.inventory.thystame >= req.thystame)

    def count_players_on_tile(self) -> int:
        tiles = self.look_around()
        if not tiles or len(tiles) == 0:
            print("AI: No tiles returned from Look, assuming self is present")
            return 1  # Le joueur lui-même est toujours présent
        current_tile = tiles[0]
        player_count = current_tile.count('player') + 1  # Inclut le joueur lui-même
        print(f"AI: Players on tile: {player_count} (including self)")
        return player_count

    def attempt_elevation(self) -> bool:
        if not self.has_elevation_resources():
            print("AI: Not enough resources for elevation")
            return False
            
        req = ELEVATION_REQUIREMENTS[self.level]
        players_on_tile = self.count_players_on_tile()
        
        print(f"AI: Attempting elevation level {self.level} (need {req.nb_players} players, have {players_on_tile})")
        
        if players_on_tile < req.nb_players:
            print(f"AI: Not enough players for elevation ({players_on_tile}/{req.nb_players})")
            return False
        
        resources_to_drop = [
            ("linemate", req.linemate),
            ("deraumere", req.deraumere),
            ("sibur", req.sibur),
            ("mendiane", req.mendiane),
            ("phiras", req.phiras),
            ("thystame", req.thystame)
        ]
        
        for resource, count in resources_to_drop:
            for _ in range(count):
                if getattr(self.inventory, resource) > 0:
                    response = self.execute_command(f"Set {resource}")
                    if response == "ok":
                        current_val = getattr(self.inventory, resource)
                        setattr(self.inventory, resource, current_val - 1)
                    else:
                        print(f"AI: Failed to set {resource}")
                        return False
        
        response = self.execute_command("Incantation")
        print(f"AI: Incantation response: {response}")
        
        if "Elevation underway" in response:
            final_response = self.network.receive_line()
            print(f"AI: Final response: {final_response}")
            
            if "Current level:" in final_response:
                try:
                    import re
                    match = re.search(r'Current level:\s*(\d+)', final_response)
                    if match:
                        old_level = self.level
                        self.level = int(match.group(1))
                        print(f"AI: Elevated from {old_level} to {self.level}!")
                        return True
                except:
                    pass
        
        print("AI: Elevation failed")
        return False

    def get_needed_resource(self) -> str:
        if self.needs_food_urgently():
            return "food"
            
        if self.level >= 8:
            return "food"
            
        req = ELEVATION_REQUIREMENTS[self.level]
        
        resources_needed = [
            ("linemate", req.linemate, self.inventory.linemate),
            ("deraumere", req.deraumere, self.inventory.deraumere),
            ("sibur", req.sibur, self.inventory.sibur),
            ("mendiane", req.deraumere >= req.mendiane),
            ("phiras", req.phiras, self.inventory.phiras),
            ("thystame", req.thystame, self.inventory.thystame)
        ]
        
        for resource_name, needed, have in resources_needed:
            if have < needed:
                return resource_name
                
        return "food"

    def start_partner_search(self):
        req = ELEVATION_REQUIREMENTS[self.level]
        if req.nb_players > 1 and not self.looking_for_partner:
            pos_x, pos_y = random.randint(0, self.world_size[0]-1), random.randint(0, self.world_size[1]-1)
            print(f"AI: Looking for partner for level {self.level} elevation at position ({pos_x}, {pos_y})")
            self.execute_command(f"Broadcast NEED_PARTNER_{self.level}_{self.client_id}_{pos_x}_{pos_y}")
            self.looking_for_partner = True
            self.partner_search_timeout = time.time() + 6
            self.just_broadcasted = True
            self.broadcast_cooldown = time.time() + 3
            self.state = "LOOKING_FOR_PARTNER"

    def simple_step(self) -> bool:
        if not self.is_alive:
            return False
            
        if time.time() - self.last_inventory_check > 5:
            if not self.update_inventory():
                return False
                
        if self.action_count % 50 == 0:
            print(f"AI: Step {self.action_count}, Food: {self.inventory.food}, Level: {self.level}, State: {self.state}")
            
        if self.looking_for_partner and time.time() > self.partner_search_timeout:
            print("AI: Partner search timeout, continuing solo")
            self.looking_for_partner = False
            self.just_broadcasted = False
            self.is_elevation_leader = False
            self.waiting_for_incantation = False
            self.leader_position = None
            if hasattr(self, 'wait_start_time'):
                delattr(self, 'wait_start_time')
            self.state = "COLLECT"
            
        if self.just_broadcasted and time.time() > self.broadcast_cooldown:
            self.just_broadcasted = False
            
        if self.needs_food_urgently():
            self.state = "SURVIVAL"
            self.target_resource = "food"
            
        elif self.state == "MOVING_TO_LEADER":
            if self.leader_position:
                _, _, direction = self.leader_position
                print(f"AI: Moving to leader in direction {direction}")
                if not self.move_to_leader(direction):
                    print("AI: Failed to move to leader, retrying")
                if random.randint(1, 20) == 1:
                    self.look_around()
            else:
                self.state = "COLLECT"
                self.waiting_for_incantation = False
            
        elif self.state == "ELEVATING" or (self.inventory.food > 15 and self.has_elevation_resources() and time.time() - self.last_elevation_attempt > 2):
            req = ELEVATION_REQUIREMENTS[self.level]
            players_on_tile = self.count_players_on_tile()
            
            if req.nb_players == 1:
                print("AI: Attempting solo elevation")
                self.last_elevation_attempt = time.time()
                if self.attempt_elevation():
                    self.state = "COLLECT"
                    self.is_elevation_leader = False
                    self.looking_for_partner = False
                    self.waiting_for_incantation = False
                else:
                    print("AI: Solo elevation failed, switching to COLLECT")
                    self.state = "COLLECT"  # Retour à COLLECT si échec
                return True
                
            elif players_on_tile >= req.nb_players:
                if self.is_elevation_leader:
                    print("AI: I'm the leader, starting group elevation protocol")
                    self.execute_command(f"Broadcast LEADER_READY_{self.level}_{self.client_id}")
                    time.sleep(0.2)
                    
                    self.execute_command(f"Broadcast STARTING_INCANTATION_{self.level}_{self.client_id}")
                    time.sleep(0.1)
                    
                    print("AI: Leader attempting group elevation")
                    self.last_elevation_attempt = time.time()
                    if self.attempt_elevation():
                        self.state = "COLLECT"
                        self.is_elevation_leader = False
                        self.looking_for_partner = False
                        self.waiting_for_incantation = False
                    else:
                        print("AI: Leader elevation failed, retrying search")
                        self.is_elevation_leader = False
                        self.looking_for_partner = False
                        self.state = "COLLECT"
                        
                elif self.waiting_for_incantation:
                    print("AI: Waiting for leader to start incantation...")
                    if random.randint(1, 20) == 1:
                        self.move_randomly()
                    
                    if not hasattr(self, 'wait_start_time'):
                        self.wait_start_time = time.time()
                    elif time.time() - self.wait_start_time > 5:
                        print("AI: Waited too long for leader, giving up")
                        self.waiting_for_incantation = False
                        self.state = "COLLECT"
                        self.leader_position = None
                        delattr(self, 'wait_start_time')
                    
                else:
                    print("AI: No clear leader, becoming leader")
                    self.is_elevation_leader = True
                    
                return True
                
            elif not self.looking_for_partner:
                self.start_partner_search()
                return True
                
        elif self.state == "LOOKING_FOR_PARTNER":
            self.move_randomly()
            
            if random.randint(1, 50) == 1 and time.time() > self.broadcast_cooldown:
                print("AI: Re-broadcasting partner search")
                pos_x, pos_y = random.randint(0, self.world_size[0]-1), random.randint(0, self.world_size[1]-1)
                self.execute_command(f"Broadcast NEED_PARTNER_{self.level}_{self.client_id}_{pos_x}_{pos_y}")
                self.broadcast_cooldown = time.time() + 3
            return True
            
        else:
            self.state = "COLLECT"
            self.target_resource = self.get_needed_resource()
            
        if not self.try_collect_resource(self.target_resource):
            self.move_randomly()
            
        self.action_count += 1
        return True

    def run(self):
        if not self.connect_to_server():
            return
            
        print(f"AI: Started for team {self.network.team_name}")
        self.update_inventory()
        
        try:
            while self.is_alive and self.level < 8:
                if not self.simple_step():
                    break
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nAI: Stopping...")
        except Exception as e:
            print(f"AI: Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("AI: Disconnecting...")
            self.network.disconnect()
        if not self.network.connect():
            print("AI: Failed to connect")
            return False
            
        success, world_size = self.network.authenticate()
        if success:
            self.world_size = world_size
            print(f"AI: Connected! World: {world_size}")
            return True
        else:
            print("AI: Authentication failed")
            return False

    def execute_command(self, command: str) -> str:
        if not self.network.send_command(command):
            self.is_alive = False
            return "dead"
        
        while True:
            response = self.network.receive_line()
            if response == "":
                time.sleep(0.01)
                continue
            if response == "dead":
                self.is_alive = False
            elif response.startswith("message"):
                self.handle_broadcast(response)
                continue
            return response

    def handle_broadcast(self, message: str):
        try:
            if ", " in message:
                parts = message.split(", ", 1)
                if len(parts) >= 2:
                    direction = int(parts[0].split()[1])
                    content = parts[1].strip()
                    
                    if direction == 0:
                        return
                    
                    if (content == f"NEED_PARTNER_{self.level}" and 
                        not self.just_broadcasted and 
                        not self.looking_for_partner and 
                        time.time() > self.broadcast_cooldown and
                        self.state == "COLLECT"):
                        
                        print(f"AI: Someone needs partner for level {self.level}, responding once")
                        self.execute_command(f"Broadcast I_AM_LEVEL_{self.level}")
                        self.broadcast_cooldown = time.time() + 3
                        self.waiting_for_incantation = True
                        self.state = "ELEVATING"
                        
                    elif content == f"I_AM_LEVEL_{self.level}" and self.looking_for_partner:
                        print(f"AI: Found partner for level {self.level}! I will be the leader.")
                        self.looking_for_partner = False
                        self.is_elevation_leader = True
                        self.state = "ELEVATING"
                        
                    elif content == f"LEADER_READY_{self.level}":
                        print(f"AI: Leader is ready for level {self.level} elevation")
                        self.waiting_for_incantation = True
                        self.state = "ELEVATING"
                        
                    elif content == f"STARTING_INCANTATION_{self.level}":
                        print(f"AI: Leader is starting incantation for level {self.level}")
                        
        except Exception as e:
            print(f"AI: Error in broadcast: {e}")

    def update_inventory(self) -> bool:
        response = self.execute_command("Inventory")
        if response and response != "dead" and response != "ko" and response != "ok":
            self.inventory = self.parser.parse_inventory(response)
            self.last_inventory_check = time.time()
            return True
        return False

    def look_around(self) -> list:
        response = self.execute_command("Look")
        if response and response != "dead" and response != "ko" and response != "ok":
            return self.parser.parse_look_result(response)
        else:
            return []

    def move_randomly(self) -> bool:
        action = random.choice(["Forward", "Left", "Right"])
        response = self.execute_command(action)
        return response == "ok"

    def try_collect_resource(self, resource: str) -> bool:
        tiles = self.look_around()
        if not tiles or len(tiles) == 0:
            return False
            
        current_tile = tiles[0]
        if resource in current_tile:
            response = self.execute_command(f"Take {resource}")
            if response == "ok":
                print(f"AI: Collected {resource}")
                if hasattr(self.inventory, resource.lower()):
                    current_val = getattr(self.inventory, resource.lower())
                    setattr(self.inventory, resource.lower(), current_val + 1)
                return True
        return False

    def needs_food_urgently(self) -> bool:
        return self.inventory.food <= 5

    def has_elevation_resources(self) -> bool:
        if self.level >= 8:
            return False
            
        req = ELEVATION_REQUIREMENTS[self.level]
        return (self.inventory.linemate >= req.linemate and
                self.inventory.deraumere >= req.deraumere and
                self.inventory.sibur >= req.sibur and
                self.inventory.mendiane >= req.mendiane and
                self.inventory.phiras >= req.phiras and
                self.inventory.thystame >= req.thystame)

    def count_players_on_tile(self) -> int:
        tiles = self.look_around()
        if not tiles or len(tiles) == 0:
            return 0
            
        current_tile = tiles[0]
        player_count = current_tile.count('player')
        return player_count

    def attempt_elevation(self) -> bool:
        if not self.has_elevation_resources():
            return False
            
        req = ELEVATION_REQUIREMENTS[self.level]
        players_on_tile = self.count_players_on_tile()
        
        print(f"AI: Attempting elevation level {self.level} (need {req.nb_players} players, have {players_on_tile})")
        
        if players_on_tile < req.nb_players:
            print(f"AI: Not enough players for elevation ({players_on_tile}/{req.nb_players})")
            return False
        
        resources_to_drop = [
            ("linemate", req.linemate),
            ("deraumere", req.deraumere),
            ("sibur", req.sibur),
            ("mendiane", req.mendiane),
            ("phiras", req.phiras),
            ("thystame", req.thystame)
        ]
        
        for resource, count in resources_to_drop:
            for _ in range(count):
                if getattr(self.inventory, resource) > 0:
                    response = self.execute_command(f"Set {resource}")
                    if response == "ok":
                        current_val = getattr(self.inventory, resource)
                        setattr(self.inventory, resource, current_val - 1)
        
        response = self.execute_command("Incantation")
        print(f"AI: Incantation response: {response}")
        
        if "Elevation underway" in response:
            final_response = self.network.receive_line()
            print(f"AI: Final response: {final_response}")
            
            if "Current level:" in final_response:
                try:
                    import re
                    match = re.search(r'Current level:\s*(\d+)', final_response)
                    if match:
                        old_level = self.level
                        self.level = int(match.group(1))
                        print(f"AI: Elevated from {old_level} to {self.level}!")
                        return True
                except:
                    pass
        
        print("AI: Elevation failed")
        return False

    def get_needed_resource(self) -> str:
        if self.needs_food_urgently():
            return "food"
            
        if self.level >= 8:
            return "food"
            
        req = ELEVATION_REQUIREMENTS[self.level]
        
        resources_needed = [
            ("linemate", req.linemate, self.inventory.linemate),
            ("deraumere", req.deraumere, self.inventory.deraumere),
            ("sibur", req.sibur, self.inventory.sibur),
            ("mendiane", req.mendiane, self.inventory.mendiane),
            ("phiras", req.phiras, self.inventory.phiras),
            ("thystame", req.thystame, self.inventory.thystame)
        ]
        
        for resource_name, needed, have in resources_needed:
            if have < needed:
                return resource_name
                
        return "food"

    def start_partner_search(self):
        req = ELEVATION_REQUIREMENTS[self.level]
        if req.nb_players > 1 and not self.looking_for_partner:
            print(f"AI: Looking for partner for level {self.level} elevation")
            self.execute_command(f"Broadcast NEED_PARTNER_{self.level}")
            self.looking_for_partner = True
            self.partner_search_timeout = time.time() + 6
            self.just_broadcasted = True
            self.broadcast_cooldown = time.time() + 3
            self.state = "LOOKING_FOR_PARTNER"

    def simple_step(self) -> bool:
        if not self.is_alive:
            return False
            
        if time.time() - self.last_inventory_check > 5:
            if not self.update_inventory():
                return False
                
        if self.action_count % 50 == 0:
            print(f"AI: Step {self.action_count}, Food: {self.inventory.food}, Level: {self.level}, State: {self.state}")
            
        if self.looking_for_partner and time.time() > self.partner_search_timeout:
            print("AI: Partner search timeout, continuing solo")
            self.looking_for_partner = False
            self.just_broadcasted = False
            self.is_elevation_leader = False
            self.waiting_for_incantation = False
            if hasattr(self, 'wait_start_time'):
                delattr(self, 'wait_start_time')
            self.state = "COLLECT"
            
        if self.just_broadcasted and time.time() > self.broadcast_cooldown:
            self.just_broadcasted = False
            
        if self.needs_food_urgently():
            self.state = "SURVIVAL"
            self.target_resource = "food"
            
        elif self.state == "ELEVATING" or (self.inventory.food > 15 and self.has_elevation_resources()):
            req = ELEVATION_REQUIREMENTS[self.level]
            players_on_tile = self.count_players_on_tile()
            
            if req.nb_players == 1:
                print("AI: Attempting solo elevation")
                if self.attempt_elevation():
                    self.state = "COLLECT"
                return True
                
            elif players_on_tile >= req.nb_players:
                if self.is_elevation_leader:
                    print("AI: I'm the leader, starting group elevation protocol")
                    self.execute_command(f"Broadcast LEADER_READY_{self.level}")
                    time.sleep(0.2)
                    
                    self.execute_command(f"Broadcast STARTING_INCANTATION_{self.level}")
                    time.sleep(0.1)
                    
                    print("AI: Leader attempting group elevation")
                    if self.attempt_elevation():
                        self.state = "COLLECT"
                        self.is_elevation_leader = False
                        self.looking_for_partner = False
                    else:
                        print("AI: Leader elevation failed, retrying search")
                        self.is_elevation_leader = False
                        self.looking_for_partner = False
                        self.state = "COLLECT"
                        
                elif self.waiting_for_incantation:
                    print("AI: Waiting for leader to start incantation...")
                    if random.randint(1, 20) == 1:
                        self.move_randomly()
                    
                    if not hasattr(self, 'wait_start_time'):
                        self.wait_start_time = time.time()
                    elif time.time() - self.wait_start_time > 5:
                        print("AI: Waited too long for leader, giving up")
                        self.waiting_for_incantation = False
                        self.state = "COLLECT"
                        delattr(self, 'wait_start_time')
                    
                else:
                    print("AI: No clear leader, becoming leader")
                    self.is_elevation_leader = True
                    
                return True
                
            elif not self.looking_for_partner:
                self.start_partner_search()
                return True
                
        elif self.state == "LOOKING_FOR_PARTNER":
            self.move_randomly()
            
            if random.randint(1, 50) == 1 and time.time() > self.broadcast_cooldown:
                print("AI: Re-broadcasting partner search")
                self.execute_command(f"Broadcast NEED_PARTNER_{self.level}")
                self.broadcast_cooldown = time.time() + 3
            return True
            
        else:
            self.state = "COLLECT"
            self.target_resource = self.get_needed_resource()
            
        if not self.try_collect_resource(self.target_resource):
            self.move_randomly()
            
        self.action_count += 1
        return True

    def run(self):
        if not self.connect_to_server():
            return
            
        print(f"AI: Started for team {self.network.team_name}")
        self.update_inventory()
        
        try:
            while self.is_alive and self.level < 8:
                if not self.simple_step():
                    break
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nAI: Stopping...")
        except Exception as e:
            print(f"AI: Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("AI: Disconnecting...")
            self.network.disconnect()