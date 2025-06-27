##
## EPITECH PROJECT, 2025
## header
## File description:
## zappy ai
##

import time
import random
import json
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
        self.last_look_result: list[list[str]] = []
        
        self.state = "INIT"
        self.target_resource = "food"
        self.commands_queue = []
        
        # Coordination pour élévations multi-joueurs
        self.is_master = False  # Celui qui a broadcast le rendez-vous
        self.rendezvous_position = None  # (x, y) du rendez-vous
        self.waiting_for_players = False
        self.elevation_timeout = 0  # Timeout pour éviter d'attendre indéfiniment
        self.current_position = (5, 5)  # Position estimée (centre par défaut)
        
        self.shared_inventory = {}
        self.client_id = random.randint(1, 1000)
        self.elevation_ready = False
        
        self.food_priority_threshold = 10
        self.last_inventory_update = 0

    def connect_to_server(self) -> bool:
        if not self.network.connect():
            print("AI: Failed to connect to network.")
            return False
        print("AI: Network connection established.")
        success, world_size = self.network.authenticate()
        if success:
            self.world_size = world_size
            print(f"AI: Authenticated. World size: {self.world_size}")
            self.state = "SURVIVE"
        else:
            print("AI: Authentication failed.")
        return success

    def execute_command(self, command: str) -> str:
        """Exécute une commande et retourne la réponse"""
        if not self.network.send_command(command):
            self.is_alive = False
            return "dead"
        
        response = self.network.receive_line()
        if response == "dead":
            self.is_alive = False
        return response

    def update_inventory(self) -> bool:
        """Met à jour l'inventaire rapidement"""
        response = self.execute_command("Inventory")
        if response and response != "dead":
            self.inventory = self.parser.parse_inventory(response)
            self.last_inventory_update = time.time()
            print(f"AI: Food={self.inventory.food}, Level={self.level}")
            return True
        return False

    def look_around(self) -> bool:
        """Regarde autour rapidement"""
        response = self.execute_command("Look")
        if response and response != "dead":
            self.last_look_result = self.parser.parse_look_result(response)
            return True
        return False

    def find_closest_resource(self, resource: str) -> int:
        """Trouve la ressource la plus proche dans la vision"""
        if not self.last_look_result:
            return -1
        
        for i, tile_objects in enumerate(self.last_look_result):
            if resource in tile_objects:
                print(f"AI: Found {resource} at tile {i}")
                return i
        return -1

    def move_to_tile(self, tile_index: int) -> bool:
        """Mouvement simplifié vers une case"""
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

    def collect_resource(self, resource: str) -> bool:
        """Collecte une ressource sur la case actuelle"""
        if not self.last_look_result or len(self.last_look_result) == 0:
            return False
        
        current_tile = self.last_look_result[0]
        if resource in current_tile:
            response = self.execute_command(f"Take {resource}")
            if response == "ok":
                if hasattr(self.inventory, resource.lower()):
                    current_val = getattr(self.inventory, resource.lower())
                    setattr(self.inventory, resource.lower(), current_val + 1)
                print(f"AI: Successfully took {resource}")
                return True
        return False

    def search_and_collect(self, resource: str) -> bool:
            """Cherche et collecte une ressource"""
            # Essayer de collecter sur la case actuelle
            if self.collect_resource(resource):
                return True
            
            # Chercher la ressource dans la vision
            tile_index = self.find_closest_resource(resource)
            if tile_index > 0:
                # Se déplacer vers la ressource trouvée
                success = self.move_to_tile(tile_index)
                if success:
                    return True
            
            # Si pas de ressource trouvée, explorer aléatoirement
            # IMPORTANT: Toujours retourner True pour continuer l'exploration
            action = random.choice(["Forward", "Left", "Right"])
            response = self.execute_command(action)
            
            # Même si le mouvement échoue, continuer (pas bloquer l'AI)
            return True  # ← CHANGEMENT IMPORTANT: toujours True

    def needs_food_urgently(self) -> bool:
        """Vérifie si on a besoin de nourriture en urgence"""
        return self.inventory.food <= self.food_priority_threshold

    def has_elevation_resources(self) -> bool:
        """Vérifie si on a les ressources pour l'élévation"""
        if self.level >= 8:
            return False
        
        required = ELEVATION_REQUIREMENTS[self.level]
        return (self.inventory.linemate >= required.linemate and
                self.inventory.deraumere >= required.deraumere and
                self.inventory.sibur >= required.sibur and
                self.inventory.mendiane >= required.mendiane and
                self.inventory.phiras >= required.phiras and
                self.inventory.thystame >= required.thystame)

    def has_total_elevation_resources(self) -> bool:
        """Vérifie si on a les ressources totales (inventaire + sol) pour l'élévation"""
        if self.level >= 8:
            return False
        
        required = ELEVATION_REQUIREMENTS[self.level]
        
        # Vérifier si on a regardé récemment
        if not self.last_look_result or len(self.last_look_result) == 0:
            return False
        
        # Case actuelle (index 0 dans look)
        current_tile = self.last_look_result[0]
        
        # Compter les ressources sur le sol
        resources_on_ground = {
            'linemate': current_tile.count('linemate'),
            'deraumere': current_tile.count('deraumere'), 
            'sibur': current_tile.count('sibur'),
            'mendiane': current_tile.count('mendiane'),
            'phiras': current_tile.count('phiras'),
            'thystame': current_tile.count('thystame')
        }
        
        # Compter les ressources totales (inventaire + sol)
        total_resources = {
            'linemate': self.inventory.linemate + resources_on_ground['linemate'],
            'deraumere': self.inventory.deraumere + resources_on_ground['deraumere'],
            'sibur': self.inventory.sibur + resources_on_ground['sibur'],
            'mendiane': self.inventory.mendiane + resources_on_ground['mendiane'],
            'phiras': self.inventory.phiras + resources_on_ground['phiras'],
            'thystame': self.inventory.thystame + resources_on_ground['thystame']
        }
        
        # Vérifier si on a assez de ressources au total
        has_enough = (total_resources['linemate'] >= required.linemate and
                     total_resources['deraumere'] >= required.deraumere and
                     total_resources['sibur'] >= required.sibur and
                     total_resources['mendiane'] >= required.mendiane and
                     total_resources['phiras'] >= required.phiras and
                     total_resources['thystame'] >= required.thystame)
        
        if not has_enough:
            print(f"AI: Missing resources for level {self.level}->{self.level+1}")
            print(f"AI: Need: linemate={required.linemate}, deraumere={required.deraumere}, sibur={required.sibur}")
            print(f"AI: Have: linemate={total_resources['linemate']}, deraumere={total_resources['deraumere']}, sibur={total_resources['sibur']}")
        
        return has_enough

    def count_players_same_level_on_tile(self) -> int:
        """Compte le nombre de joueurs du même niveau sur la case actuelle"""
        if not self.last_look_result or len(self.last_look_result) == 0:
            return 0
        
        current_tile = self.last_look_result[0]
        # Compter le nombre de "player" sur la case
        player_count = current_tile.count('player')
        
        # On compte nous-même, donc on a au moins 1 joueur de notre niveau
        return player_count

    def can_attempt_elevation(self) -> bool:
        """Vérifie toutes les conditions pour tenter une élévation"""
        if self.level >= 8:
            return False
        
        required = ELEVATION_REQUIREMENTS[self.level]
        
        # 1. Vérifier qu'on a assez de nourriture pour survivre à l'élévation (300 time units)
        food_needed_for_elevation = 300 // 126 + 10  # +10 pour plus de sécurité
        if self.inventory.food < food_needed_for_elevation:
            print(f"AI: Not enough food for elevation. Need {food_needed_for_elevation}, have {self.inventory.food}")
            return False
        
        # 2. Vérifier le nombre de joueurs requis sur la case
        players_on_tile = self.count_players_same_level_on_tile()
        if players_on_tile < required.nb_players:
            print(f"AI: Not enough players on tile. Need {required.nb_players}, have {players_on_tile}")
            return False
        
        # 3. Vérifier qu'on a assez de ressources (inventaire + sol) pour l'élévation
        if not self.has_total_elevation_resources():
            print(f"AI: Not enough total resources for elevation level {self.level}")
            return False
        
        print(f"AI: All conditions met for elevation level {self.level} -> {self.level + 1}")
        return True

    def attempt_elevation_improved(self) -> bool:
        """Version améliorée de la tentative d'élévation"""
        if not self.can_attempt_elevation():
            return False
        
        print(f"AI: Starting elevation process from level {self.level}")
        
        # Pour les élévations de groupe, ne pas déposer TOUTES nos ressources
        # Juste s'assurer qu'il y en a assez sur le sol
        required = ELEVATION_REQUIREMENTS[self.level]
        
        if required.nb_players > 1:
            # Élévation de groupe - vérifier qu'il y a assez sur le sol
            print("AI: Group elevation - checking ground resources...")
            
            if not self.look_around():
                print("AI: Failed to look around")
                return False
            
            current_tile = self.last_look_result[0] if self.last_look_result else []
            resources_on_ground = {
                'linemate': current_tile.count('linemate'),
                'deraumere': current_tile.count('deraumere'), 
                'sibur': current_tile.count('sibur'),
                'mendiane': current_tile.count('mendiane'),
                'phiras': current_tile.count('phiras'),
                'thystame': current_tile.count('thystame')
            }
            
            print(f"AI: Resources on ground before elevation: {resources_on_ground}")
            
            # Si on n'a pas assez, déposer nos propres ressources
            resources_to_drop = [
                ("linemate", max(0, required.linemate - resources_on_ground['linemate'])),
                ("deraumere", max(0, required.deraumere - resources_on_ground['deraumere'])),
                ("sibur", max(0, required.sibur - resources_on_ground['sibur'])),
                ("mendiane", max(0, required.mendiane - resources_on_ground['mendiane'])),
                ("phiras", max(0, required.phiras - resources_on_ground['phiras'])),
                ("thystame", max(0, required.thystame - resources_on_ground['thystame']))
            ]
            
            print("AI: Dropping missing resources...")
            for resource, count in resources_to_drop:
                for _ in range(count):
                    if getattr(self.inventory, resource) > 0:
                        response = self.execute_command(f"Set {resource}")
                        if response == "ok":
                            current_val = getattr(self.inventory, resource)
                            setattr(self.inventory, resource, current_val - 1)
                            print(f"AI: Dropped {resource}, remaining: {getattr(self.inventory, resource)}")
        else:
            # Élévation solo - déposer toutes les ressources requises
            print("AI: Solo elevation - dropping all required resources...")
            resources_to_drop = [
                ("linemate", required.linemate),
                ("deraumere", required.deraumere),
                ("sibur", required.sibur),
                ("mendiane", required.mendiane),
                ("phiras", required.phiras),
                ("thystame", required.thystame)
            ]
            
            for resource, count in resources_to_drop:
                for _ in range(count):
                    if getattr(self.inventory, resource) > 0:
                        response = self.execute_command(f"Set {resource}")
                        if response == "ok":
                            current_val = getattr(self.inventory, resource)
                            setattr(self.inventory, resource, current_val - 1)
                            print(f"AI: Dropped {resource}, remaining: {getattr(self.inventory, resource)}")
        
        # Tenter l'incantation
        print("AI: Attempting incantation...")
        response = self.execute_command("Incantation")
        print(f"AI: Incantation response: {response}")
        
        if "Elevation underway" in response:
            print("AI: Elevation started successfully!")
            
            # Attendre la fin de l'élévation
            final_response = self.network.receive_line()
            print(f"AI: Final elevation response: {final_response}")
            
            if "Current level:" in final_response:
                try:
                    new_level = int(''.join(filter(str.isdigit, final_response)))
                    old_level = self.level
                    self.level = new_level
                    print(f"AI: Successfully elevated from level {old_level} to level {self.level}!")
                    return True
                except:
                    print("AI: Failed to parse new level")
                    return False
            else:
                print(f"AI: Elevation failed with response: {final_response}")
                return False
        else:
            print(f"AI: Elevation failed to start: {response}")
            # Debug: regarder le sol après l'échec
            self.look_around()
            if self.last_look_result:
                print(f"AI: Ground after failed elevation: {self.last_look_result[0]}")
            return False
    
    def get_most_needed_resource(self) -> str:
        """Détermine quelle ressource collecter en priorité pour l'élévation"""
        if self.level >= 8:
            return "food"
        
        required = ELEVATION_REQUIREMENTS[self.level]
        
        # Vérifier chaque ressource et retourner la première manquante
        resources_to_check = [
            ("linemate", required.linemate, self.inventory.linemate),
            ("deraumere", required.deraumere, self.inventory.deraumere), 
            ("sibur", required.sibur, self.inventory.sibur),
            ("mendiane", required.mendiane, self.inventory.mendiane),
            ("phiras", required.phiras, self.inventory.phiras),
            ("thystame", required.thystame, self.inventory.thystame)
        ]
        
        for resource_name, needed, have in resources_to_check:
            if have < needed:
                print(f"AI: Need more {resource_name}: have {have}, need {needed}")
                return resource_name
        
        # Si on a tout pour l'élévation actuelle, on peut viser le niveau suivant
        if self.level < 7:
            next_required = ELEVATION_REQUIREMENTS[self.level + 1]
            for resource_name, needed, have in [
                ("linemate", next_required.linemate, self.inventory.linemate),
                ("deraumere", next_required.deraumere, self.inventory.deraumere),
                ("sibur", next_required.sibur, self.inventory.sibur),
                ("mendiane", next_required.mendiane, self.inventory.mendiane), 
                ("phiras", next_required.phiras, self.inventory.phiras),
                ("thystame", next_required.thystame, self.inventory.thystame)
            ]:
                if have < needed:
                    return resource_name
        
        return "food"

    def is_ready_for_elevation(self) -> bool:
        """Vérifie si on est prêt à initier une élévation multi-joueurs"""
        if self.level >= 8:
            return False
        
        required = ELEVATION_REQUIREMENTS[self.level]
        
        # Pour level 1->2, pas besoin de coordination (1 seul joueur)
        if required.nb_players == 1:
            return False
        
        # Vérifier qu'on a assez de food
        food_needed = 300 // 126 + 15
        if self.inventory.food < food_needed:
            return False
        
        # Vérifier qu'on a les ressources pour l'élévation
        return self.has_total_elevation_resources()

    def broadcast_rendezvous(self) -> bool:
        """Broadcast un rendez-vous pour élévation"""
        if not self.is_ready_for_elevation():
            return False
        
        # Utiliser notre position actuelle comme point de rendez-vous
        x, y = self.current_position
        message = f"RENDEZ_VOUS:{self.level}:{x}:{y}:{self.client_id}"
        
        print(f"AI: Broadcasting rendezvous at ({x}, {y}) for level {self.level}")
        response = self.execute_command(f"Broadcast {message}")
        
        if response == "ok":
            self.is_master = True
            self.rendezvous_position = (x, y)
            self.waiting_for_players = True
            self.elevation_timeout = time.time() + 30  # 30 secondes timeout
            self.state = "WAITING_FOR_PLAYERS"
            print(f"AI: Now waiting for {ELEVATION_REQUIREMENTS[self.level].nb_players} players")
            return True
        
        return False

    def check_for_broadcasts(self):
            """Vérifie s'il y a des broadcasts à traiter (version améliorée)"""
            try:
                # Essayer de recevoir un message sans bloquer
                message = self.network.receive_line()
                if message and message.strip():
                    print(f"AI: Received message: '{message}'")
                    
                    if message.startswith("message"):
                        print(f"AI: Processing broadcast: {message}")
                        self.parse_broadcast_message(message)
                    elif message == "dead":
                        print("AI: Received death message!")
                        self.is_alive = False
                        return False
                    # Ignorer les autres messages (ok, ko, etc.)
                    
            except Exception as e:
                # Pas de message disponible, continuer normalement
                pass
            return True

    def parse_broadcast_message(self, message: str):
        """Parse un message broadcast reçu"""
        if not message.startswith("message"):
            return
        
        try:
            # Format: "message 3, RENDEZ_VOUS:2:5:7:1234"
            parts = message.split(", ", 1)
            if len(parts) < 2:
                return
            
            direction = int(parts[0].split()[1])
            content = parts[1]
            
            if content.startswith("RENDEZ_VOUS:"):
                self.handle_rendezvous_broadcast(content, direction)
                
        except Exception as e:
            print(f"AI: Error parsing broadcast: {e}")

    def handle_rendezvous_broadcast(self, content: str, direction: int):
        """Gère la réception d'un broadcast de rendez-vous"""
        try:
            # Format: "RENDEZ_VOUS:level:x:y:client_id"
            parts = content.split(":")
            if len(parts) < 5:
                return
            
            broadcast_level = int(parts[1])
            x = int(parts[2])
            y = int(parts[3])
            broadcaster_id = int(parts[4])
            
            # Ignorer notre propre broadcast
            if broadcaster_id == self.client_id:
                return
            
            # Ignorer si pas le même niveau
            if broadcast_level != self.level:
                print(f"AI: Ignoring broadcast for level {broadcast_level} (I'm level {self.level})")
                return
            
            # Ignorer si on n'est pas prêt pour une élévation
            if not self.is_ready_for_elevation():
                print(f"AI: Received rendezvous but not ready yet")
                return
            
            # Ignorer si on est déjà master ou en cours d'attente
            if self.is_master or self.waiting_for_players:
                print(f"AI: Ignoring broadcast - already coordinating")
                return
            
            print(f"AI: Received rendezvous invitation for level {broadcast_level} at ({x}, {y})")
            self.rendezvous_position = (x, y)
            self.state = "GOING_TO_RENDEZVOUS"
            
        except Exception as e:
            print(f"AI: Error handling rendezvous broadcast: {e}")

    def move_towards_position(self, target_x: int, target_y: int) -> bool:
        """Se déplace vers une position cible (version simplifiée)"""
        # Pour l'instant, on fait des mouvements aléatoires vers la cible
        # Dans un vrai jeu, on implémenterait un pathfinding
        
        current_x, current_y = self.current_position
        
        # Si on est arrivé (ou très proche)
        if abs(current_x - target_x) <= 1 and abs(current_y - target_y) <= 1:
            self.current_position = (target_x, target_y)
            return True
        
        # Mouvement simple vers la cible
        moved = False
        if random.choice([True, False]):  # Choisir x ou y aléatoirement
            if current_x < target_x:
                if self.execute_command("Forward") == "ok":
                    self.current_position = (current_x + 1, current_y)
                    moved = True
            elif current_x > target_x:
                if self.execute_command("Forward") == "ok":
                    self.current_position = (current_x - 1, current_y)
                    moved = True
        else:
            if current_y < target_y:
                if self.execute_command("Forward") == "ok":
                    self.current_position = (current_x, current_y + 1)
                    moved = True
            elif current_y > target_y:
                if self.execute_command("Forward") == "ok":
                    self.current_position = (current_x, current_y - 1)
                    moved = True
        
        if not moved:
            # Si on n'a pas bougé, faire un mouvement aléatoire
            action = random.choice(["Forward", "Left", "Right"])
            self.execute_command(action)
        
        return False

    def check_elevation_timeout(self) -> bool:
        """Vérifie si le timeout d'élévation est dépassé"""
        if self.waiting_for_players and time.time() > self.elevation_timeout:
            print("AI: Elevation timeout - resuming normal activities")
            self.reset_elevation_state()
            return True
        return False

    def reset_elevation_state(self):
        """Remet à zéro l'état d'élévation"""
        self.is_master = False
        self.rendezvous_position = None
        self.waiting_for_players = False
        self.elevation_timeout = 0
        self.state = "COLLECT"

    def handle_waiting_for_players(self) -> bool:
            """Gère l'état d'attente des autres joueurs"""
            if not self.rendezvous_position:
                self.reset_elevation_state()
                return True
            
            # Vérifier si on a assez de joueurs sur notre case
            players_on_tile = self.count_players_same_level_on_tile()
            required = ELEVATION_REQUIREMENTS[self.level]
            
            print(f"AI: Waiting for players - have {players_on_tile}, need {required.nb_players}")
            
            if players_on_tile >= required.nb_players:
                # NOUVEAU: Vérifier les ressources avant de tenter l'élévation
                print("AI: Enough players gathered - checking resources before elevation...")
                
                # Regarder le sol pour voir ce qu'il y a
                if not self.look_around():
                    print("AI: Failed to look around")
                    return True
                
                current_tile = self.last_look_result[0] if self.last_look_result else []
                print(f"AI: Current tile contents: {current_tile}")
                
                # Vérifier les ressources sur le sol
                resources_on_ground = {
                    'linemate': current_tile.count('linemate'),
                    'deraumere': current_tile.count('deraumere'), 
                    'sibur': current_tile.count('sibur'),
                    'mendiane': current_tile.count('mendiane'),
                    'phiras': current_tile.count('phiras'),
                    'thystame': current_tile.count('thystame')
                }
                
                print(f"AI: Resources on ground: {resources_on_ground}")
                print(f"AI: Need for level {self.level}: linemate={required.linemate}, deraumere={required.deraumere}, sibur={required.sibur}")
                
                # Vérifier si on a tout ce qu'il faut
                if (resources_on_ground['linemate'] >= required.linemate and
                    resources_on_ground['deraumere'] >= required.deraumere and
                    resources_on_ground['sibur'] >= required.sibur and
                    resources_on_ground['mendiane'] >= required.mendiane and
                    resources_on_ground['phiras'] >= required.phiras and
                    resources_on_ground['thystame'] >= required.thystame):
                    
                    print("AI: All resources available on ground - attempting group elevation!")
                    success = self.attempt_elevation_improved()
                    self.reset_elevation_state()
                    return success
                else:
                    print("AI: Not enough resources on ground yet - waiting more...")
                    # Broadcast pour demander aux autres de déposer leurs ressources
                    self.execute_command(f"Broadcast NEED_RESOURCES:{self.level}")
                    return True
            else:
                # Continuer à attendre, mais bouger un peu pour rester actif
                if random.randint(1, 10) == 1:
                    action = random.choice(["Left", "Right"])
                    self.execute_command(action)
                return True

    def handle_going_to_rendezvous(self) -> bool:
        """Gère l'état de déplacement vers le rendez-vous"""
        if not self.rendezvous_position:
            self.state = "COLLECT"
            return True
        
        target_x, target_y = self.rendezvous_position
        
        # Vérifier si on est arrivé
        if abs(self.current_position[0] - target_x) <= 1 and abs(self.current_position[1] - target_y) <= 1:
            print("AI: Arrived at rendezvous point - waiting for elevation")
            self.state = "WAITING_FOR_PLAYERS"
            self.waiting_for_players = True
            self.elevation_timeout = time.time() + 20  # 20 secondes d'attente
            return True
        
        # Se déplacer vers le rendez-vous
        print(f"AI: Moving towards rendezvous at ({target_x}, {target_y}) from {self.current_position}")
        return self.move_towards_position(target_x, target_y)

    def broadcast_inventory(self):
        """Partage l'inventaire avec l'équipe"""
        try:
            inventory_data = {
                "food": self.inventory.food,
                "linemate": self.inventory.linemate,
                "deraumere": self.inventory.deraumere,
                "sibur": self.inventory.sibur,
                "mendiane": self.inventory.mendiane,
                "phiras": self.inventory.phiras,
                "thystame": self.inventory.thystame
            }
            message = f"INV:{self.client_id}:{self.level}:{json.dumps(inventory_data)}"
            self.execute_command(f"Broadcast {message}")
        except:
            pass

    def main_loop_step(self) -> bool:
        """Une étape améliorée de la boucle principale avec coordination"""
        
        # Vérifier les timeouts
        if self.check_elevation_timeout():
            return True
        
        # Écouter les broadcasts (version non-bloquante)
        self.check_for_broadcasts()
        
        # Mise à jour périodique de l'inventaire
        if time.time() - self.last_inventory_update > 3:
            if not self.update_inventory():
                return False
        
        # Toujours regarder autour pour avoir des infos fraîches
        if not self.look_around():
            return False
        
        # Debug: afficher l'état actuel
        print(f"AI: State={self.state}, Food={self.inventory.food}, Level={self.level}")
        
        # Priorité 1: Survie (nourriture critique)
        if self.needs_food_urgently():
            print("AI: URGENT - Need food!")
            self.target_resource = "food"
            self.state = "SURVIVE"
            self.search_and_collect(self.target_resource)  # ← Pas de check du résultat
            return True  # ← Toujours continuer
        
        # Priorité 2: États de coordination
        if self.state == "WAITING_FOR_PLAYERS":
            print("AI: In WAITING_FOR_PLAYERS state")
            return self.handle_waiting_for_players()
        
        if self.state == "GOING_TO_RENDEZVOUS":
            print("AI: In GOING_TO_RENDEZVOUS state")
            return self.handle_going_to_rendezvous()
        
        # Priorité 3: Tentative d'élévation solo (level 1->2)
        if self.inventory.food > 20 and self.can_attempt_elevation():
            required = ELEVATION_REQUIREMENTS[self.level]
            if required.nb_players == 1:  # Élévation solo
                print("AI: Solo elevation conditions met - attempting elevation!")
                success = self.attempt_elevation_improved()
                if success:
                    self.state = "COLLECT"
                    return True
                else:
                    print("AI: Solo elevation failed, continuing with resource collection")
                    self.state = "COLLECT"
        
        # Priorité 4: Initier une coordination multi-joueurs
        if self.inventory.food > 25 and self.is_ready_for_elevation():
            required = ELEVATION_REQUIREMENTS[self.level]
            if required.nb_players > 1 and not self.waiting_for_players:
                print(f"AI: Ready for multi-player elevation (need {required.nb_players} players)")
                if self.broadcast_rendezvous():
                    return True
        
        # Priorité 5: Collection de ressources pour l'élévation
        if self.inventory.food > 15:
            missing_resource = self.get_most_needed_resource()
            if missing_resource != "food":
                self.target_resource = missing_resource
                self.state = "COLLECT"
                print(f"AI: Collecting {missing_resource} for future elevation")
                self.search_and_collect(self.target_resource)  # ← Pas de check du résultat
                return True  # ← Toujours continuer
        
        # Priorité 6: Collecter de la nourriture si on en a pas assez
        print("AI: Collecting more food")
        self.target_resource = "food"
        self.state = "SURVIVE"
        self.search_and_collect(self.target_resource)  # ← Pas de check du résultat
        return True  # ← Toujours continuer

    def run(self):
        if not self.connect_to_server():
            print("AI: Could not connect to server. Exiting.")
            return

        print(f"AI: Successfully started for team {self.network.team_name}")
        
        self.update_inventory()

        try:
            step_count = 0
            while self.is_alive and self.level < 8:
                if not self.main_loop_step():
                    print("AI: Main loop step failed")
                    break
                
                step_count += 1
                if step_count % 50 == 0:
                    print(f"AI: Step {step_count}, Food: {self.inventory.food}, Level: {self.level}")
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nAI: Keyboard interrupt detected. Stopping AI.")
        except Exception as e:
            print(f"AI: An error occurred during run: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("AI: Disconnecting...")
            self.network.disconnect()