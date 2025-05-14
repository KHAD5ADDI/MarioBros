# GuidedAgent.py

import numpy as np
import random
import pygame
import os
import pickle
import cv2  # Pour la détection du checkpoint

class GuidedAgent:
    """
    Agent guidé pour Super Mario Python
    
    Cet agent utilise des informations structurées sur l'environnement
    pour prendre des décisions plus informées et peut apprendre de ses erreurs
    grâce à l'apprentissage par renforcement.
    """
    
    def __init__(self):
        # Paramètres de l'agent
        self.exploration_rate = 0.4  # Taux d'exploration initial augmenté pour plus d'exploration
        self.min_exploration_rate = 0.05  # Taux minimal d'exploration
        self.exploration_decay = 0.99  # Taux de décroissance de l'exploration ralenti
        
        # Initialiser les poids pour différentes caractéristiques
        self.weights = {
            "distance_to_enemy": -2.0,  # Pénalité pour être proche d'un ennemi
            "distance_to_coin": 1.5,    # Récompense pour être proche d'une pièce
            "forward_progress": 3.0,    # Préférence pour avancer
            "jump_over_gap": 5.0,       # Récompense pour sauter par-dessus un trou
            "jump_over_enemy": 4.5,     # Récompense pour sauter par-dessus un ennemi
        }
        
        # Historique des actions et états
        self.last_action = None
        self.last_position = (0, 0)
        self.position_history = []  # Garder trace des dernières positions
        
        # Variables supplémentaires pour améliorer la prise de décision
        self.jump_cooldown = 0
        self.consecutive_same_actions = 0
        self.stuck_counter = 0
        self.right_bias_counter = 0  # Pour favoriser le mouvement vers la droite
        
        # Variables pour alterner les actions en cas de blocage
        self.force_alternate = False
        self.alternating_actions = ['jump', 'right', 'jump', 'right', 'jump']
        self.alternating_index = 0
        
        # Compteur pour les menus
        self.menu_action_counter = 0
        
        # Mémoire d'apprentissage par renforcement AMÉLIORÉE
        self.learning_rate = 0.15  # Augmenté pour un apprentissage plus rapide
        self.discount_factor = 0.95  # Augmenté pour valoriser davantage les récompenses futures
        self.q_table = {}  # Table Q pour stocker les valeurs d'action-état
        self.experience_buffer = []  # Tampon d'expérience pour l'apprentissage
        self.max_buffer_size = 2000  # Taille maximale du tampon augmentée
        
        # Historique des performances pour l'apprentissage à long terme
        self.episode_rewards = []
        self.max_distance_reached = 0
        self.previous_experiences = {}  # Pour stocker les expériences importantes par état
        
        # NOUVELLE FONCTIONNALITÉ: Mémoire des zones dangereuses et des actions à éviter
        self.death_locations = {}  # Dictionnaire pour stocker les positions où Mario est mort
        self.death_actions = {}    # Actions qui ont conduit à la mort dans des positions spécifiques
        self.location_attempts = {}  # Nombre de tentatives dans chaque location
        self.location_strategy = {}  # Stratégie spécifique à utiliser pour chaque location problématique
        self.death_count = 0       # Compteur de morts total
        
        # Charger la table Q si elle existe
        self.model_path = "ai_memory.pkl"
        self.load_memory()
        
        # Chargement de l'image de checkpoint pour la détection
        checkpoint_path = os.path.join("img", "checkpoint.jpg")
        if os.path.exists(checkpoint_path):
            self.checkpoint_image = cv2.imread(checkpoint_path)
            if self.checkpoint_image is not None:
                self.checkpoint_image = cv2.cvtColor(self.checkpoint_image, cv2.COLOR_BGR2RGB)
                print("Image de checkpoint chargée avec succès")
            else:
                print("Erreur lors du chargement de l'image de checkpoint")
                self.checkpoint_image = None
        else:
            print(f"Image de checkpoint non trouvée à {checkpoint_path}")
            self.checkpoint_image = None
            
        # Compteur de parties et statistiques
        self.game_count = 0
        self.wins = 0
        self.losses = 0
        self.max_score = 0
        self.total_distance = 0
        self.last_episode_state = None
        self.last_episode_action = None
        
        print("Agent guidé initialisé avec paramètres d'apprentissage améliorés et mémoire des zones dangereuses")
        
    def choose_action(self, state):
        """
        Sélectionne une action en fonction de l'état actuel
        """
        try:
            # Actions possibles
            actions = ['left', 'right', 'jump', 'idle']
            
            # Vérifier l'état du jeu
            game_state = state.get("game_state", "playing")
            
            # Logique spécifique pour le menu
            if game_state == "menu":
                return self.handle_menu_action()
                
            # Logique pour le game over
            if game_state == "game_over":
                # Mémoriser la position de la mort si on a les infos nécessaires
                if self.last_position != (0, 0) and self.last_action is not None:
                    # Arrondir la position pour créer une zone
                    death_zone = (int(self.last_position[0] / 50) * 50, int(self.last_position[1] / 50) * 50)
                    death_key = f"{death_zone[0]}-{death_zone[1]}"
                    
                    # Incrémenter le compteur de morts
                    self.death_count += 1
                    
                    # Enregistrer la position et l'action qui a conduit à la mort
                    if death_key not in self.death_locations:
                        self.death_locations[death_key] = 1
                        self.death_actions[death_key] = {self.last_action: 1}
                        self.location_attempts[death_key] = {a: 0 for a in actions}
                        # Stratégie initiale: essayer d'autres actions
                        self.location_strategy[death_key] = [a for a in actions if a != self.last_action]
                        random.shuffle(self.location_strategy[death_key])
                        
                        print(f"Nouvelle zone de mort enregistrée: {death_key}, action: {self.last_action}")
                    else:
                        # Mettre à jour les statistiques
                        self.death_locations[death_key] += 1
                        if self.last_action in self.death_actions[death_key]:
                            self.death_actions[death_key][self.last_action] += 1
                        else:
                            self.death_actions[death_key][self.last_action] = 1
                            
                        # Mise à jour de la stratégie basée sur l'historique des morts
                        # Privilégier les actions qui ont causé le moins de morts
                        sorted_actions = sorted(self.death_actions[death_key].items(), 
                                              key=lambda x: x[1])
                        best_actions = [a[0] for a in sorted_actions[:2]]  # Les 2 meilleures actions
                        
                        # S'assurer que toutes les actions sont essayées au moins une fois
                        for a in actions:
                            if a not in self.death_actions[death_key]:
                                best_actions.append(a)
                                
                        # Mise à jour de la stratégie pour cette zone
                        self.location_strategy[death_key] = best_actions
                        
                        print(f"Zone de mort mise à jour: {death_key}, morts: {self.death_locations[death_key]}")
                        print(f"Actions qui ont conduit à la mort: {self.death_actions[death_key]}")
                        print(f"Nouvelle stratégie: {self.location_strategy[death_key]}")
                
                # Après game over, préférer l'action jump pour redémarrer
                return 'jump'
            
            # Récupérer la position actuelle de Mario
            mario_pos = state["mario_pos"]
            
            # Vérifier si Mario est dans une zone connue comme dangereuse
            current_zone = (int(mario_pos[0] / 50) * 50, int(mario_pos[1] / 50) * 50)
            zone_key = f"{current_zone[0]}-{current_zone[1]}"
            
            # Si Mario est dans une zone où il est déjà mort, utiliser une stratégie spécifique
            if zone_key in self.death_locations and random.random() < 0.7:  # 70% de chance d'appliquer la stratégie
                # Incrémenter le compteur de tentatives pour cette zone
                if zone_key in self.location_attempts:
                    attempts = sum(self.location_attempts[zone_key].values())
                    
                    # Choisir une action basée sur la stratégie pour cette zone
                    if self.location_strategy[zone_key]:
                        # Utiliser une stratégie cyclique pour essayer différentes actions
                        strategy_index = attempts % len(self.location_strategy[zone_key])
                        chosen_action = self.location_strategy[zone_key][strategy_index]
                        
                        # Enregistrer cette tentative
                        if chosen_action in self.location_attempts[zone_key]:
                            self.location_attempts[zone_key][chosen_action] += 1
                        else:
                            self.location_attempts[zone_key][chosen_action] = 1
                            
                        print(f"Zone dangereuse détectée: {zone_key}, morts: {self.death_locations[zone_key]}")
                        print(f"Application de la stratégie spécifique: action {chosen_action} (tentative {attempts+1})")
                        self.last_action = chosen_action
                        return chosen_action
            
            # Forcer un mouvement vers la droite régulièrement pour garantir la progression
            action_counter = getattr(self, 'action_counter', 0)
            self.action_counter = action_counter + 1
            
            # Forcer un mouvement vers la droite presque systématiquement (sauf en cas d'obstacle)
            if self.action_counter % 3 == 0:
                print("FORÇAGE DE DÉPLACEMENT VERS LA DROITE")
                self.action_counter = 0
                self.last_action = 'right'
                return 'right'
            
            # SUPPRIMÉ: Ne plus forcer de saut occasionnel
            # if self.action_counter % 7 == 0:
            #     print("FORÇAGE DE SAUT OCCASIONNEL")
            #     self.last_action = 'jump'
            #     return 'jump'
            
            # Si on est en mode alternance forcée (pour débloquer Mario)
            if self.force_alternate:
                action = self.alternating_actions[self.alternating_index]
                self.alternating_index = (self.alternating_index + 1) % len(self.alternating_actions)
                
                # Sortir du mode alternance après un cycle complet
                if self.alternating_index == 0:
                    self.force_alternate = False
                
                print(f"Action forcée (alternance): {action}")
                return action
            
            # Explorer avec une certaine probabilité (epsilon-greedy)
            if random.random() < self.exploration_rate:
                # Privilégier davantage le mouvement vers la droite, réduire les sauts en exploration
                jump_probability = 0.2  # Réduit à 20% de chances de sauter
                if random.random() < jump_probability:
                    action = 'jump'
                else:
                    # Favoriser fortement le mouvement vers la droite
                    action = random.choice(['right', 'right', 'right', 'right', 'right', 'left'])  # 85% chance de droite
                print(f"Action aléatoire: {action}")
                return action
            
            # Gérer les événements pygame
            pygame.event.pump()
            
            # Récupérer les informations d'état
            mario_vel = state["mario_vel"]
            nearby_objects = state["nearby_objects"]
            
            # DEBUG: vérifier si Mario est au sol
            is_on_ground = mario_vel[1] == 0
            print(f"Mario est au sol: {is_on_ground}")
            
            # SUPPRIMÉ: Ne plus favoriser le saut systématiquement quand Mario est au sol
            # if is_on_ground and random.random() < 0.3:
            #     print("Saut favorisé car Mario est au sol!")
            #     self.last_action = 'jump'
            #     return 'jump'
            
            # Afficher des informations de débogage (réduites)
            print(f"Position: {mario_pos}, Vitesse: {mario_vel}, Objets: {len(nearby_objects)}")
            
            # Calculer les scores pour chaque action avec un meilleur équilibre
            action_scores = {
                'left': 0,
                'right': self.weights["forward_progress"] * 2.5,  # Augmenté pour privilégier l'avancement
                'jump': -2.0,  # Valeur de base négative pour éviter les sauts inutiles
                'idle': 0
            }
            
            # Limiter le cooldown du saut pour permettre des sauts mais pas trop fréquents
            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
                action_scores['jump'] -= 5.0  # Pénalité plus forte pendant le cooldown
            
            # Détecter les ennemis à l'avant
            enemies_ahead = False
            enemies_close = False
            
            # Analyser les objets proches
            ground_tiles_ahead = []
            ground_tiles_below = []
            coins_above = False
            blocks_ahead = False  # NOUVEAU: Détection des blocs devant Mario
            
            for obj in nearby_objects:
                rel_x, rel_y, obj_type = obj
                
                # Détecter les ennemis
                if "Goomba" in obj_type or "Koopa" in obj_type:
                    if 0 < rel_x < 80 and abs(rel_y) < 50:  # Ennemi à droite proche
                        enemies_ahead = True
                        if rel_x < 40:  # Très proche
                            enemies_close = True
                            action_scores['jump'] += self.weights["jump_over_enemy"] * 2.0
                            print("OBSTACLE: Ennemi très proche, je saute!")
                        else:
                            action_scores['jump'] += self.weights["jump_over_enemy"] * 1.5
                            print("OBSTACLE: Ennemi détecté devant, je saute!")
                
                # Détecter les objets à collecter
                if any(item in obj_type for item in ["Coin", "CoinBox", "RandomBox", "Mushroom"]):
                    # Item au-dessus de Mario
                    if abs(rel_x) < 16 and -150 < rel_y < -20:
                        coins_above = True
                        action_scores['jump'] += self.weights["distance_to_coin"] * 2.0
                        print("OBSTACLE: Bonus au-dessus, je saute!")
                    # Item devant Mario
                    elif 0 < rel_x < 100:
                        action_scores['right'] += self.weights["distance_to_coin"] * 1.5
                
                # NOUVEAU: Détecter les blocs devant Mario qui nécessitent un saut
                if "Tile" in obj_type or "Block" in obj_type or "Brick" in obj_type:
                    # Tuiles directement devant Mario à hauteur de son corps
                    if 10 < rel_x < 40 and -40 < rel_y < 5:
                        blocks_ahead = True
                        action_scores['jump'] += 10.0  # Bonus important pour sauter
                        print("OBSTACLE: Bloc devant Mario, je dois sauter!")
                    
                    # Tuiles directement sous Mario
                    if abs(rel_x) < 16 and 0 < rel_y < 32:
                        ground_tiles_below.append(obj)
                    # Tuiles devant Mario (pour détecter les trous)
                    elif 16 < rel_x < 96 and -10 < rel_y < 40:
                        ground_tiles_ahead.append(obj)
            
            # Vérifier s'il y a un sol devant (sinon, c'est un trou)
            if len(ground_tiles_ahead) == 0 and mario_vel[0] >= 0:
                # Pas de sol détecté devant = probablement un trou
                action_scores['jump'] += self.weights["jump_over_gap"] * 3
                print("OBSTACLE: Trou détecté, je saute!")
                # Forcer le saut directement si un trou est détecté
                return 'jump'
            
            # Si un obstacle est détecté devant, sauter est prioritaire
            if blocks_ahead or enemies_ahead:
                print("Obstacle confirmé devant Mario, saut nécessaire!")
                if self.jump_cooldown <= 0 and is_on_ground:
                    self.last_action = 'jump'
                    self.jump_cooldown = 15  # Empêcher les sauts répétés
                    return 'jump'
            
            # Gérer le cas où Mario est bloqué
            current_pos = tuple(mario_pos)
            self.position_history.append(current_pos)
            if len(self.position_history) > 20:
                self.position_history.pop(0)
            
            # Calculer le mouvement récent
            recent_movement = 0
            if len(self.position_history) > 10:
                recent_movement = abs(self.position_history[-1][0] - self.position_history[0][0])
            
            # Si Mario n'a pas bougé significativement récemment
            if recent_movement < 10:
                self.stuck_counter += 1
                print(f"Peu de mouvement récent: {recent_movement}, compteur bloqué: {self.stuck_counter}")
                
                if self.stuck_counter > 3:
                    print("Je semble bloqué, je vais alterner des actions pour me débloquer")
                    # Alterner entre avancer et sauter pour se débloquer
                    self.force_alternate = True
                    # Séquence d'alternance avec plus de mouvements vers la droite
                    self.alternating_actions = ['right', 'jump', 'right', 'right', 'jump', 'right']
                    self.alternating_index = 0
                    self.stuck_counter = 0
                    return 'right'  # Commencer par avancer pour se débloquer
            else:
                self.stuck_counter = max(0, self.stuck_counter - 1)
            
            # SUPPRIMÉ: Ne plus ajouter de facteur aléatoire pour les sauts exploratoires
            # if random.random() < 0.1:
            #     print("Saut aléatoire exploratoire!")
            #     self.last_action = 'jump'
            #     return 'jump'
            
            # Si Mario vient de sauter, favoriser l'action "right" juste après
            if self.last_action == 'jump':
                action_scores['right'] += 5.0  # Augmenté pour s'assurer de continuer à avancer après un saut
                self.right_bias_counter = 8  # Augmenté pour favoriser "right" plus longtemps après un saut
            
            if self.right_bias_counter > 0:
                action_scores['right'] += 3.0
                self.right_bias_counter -= 1
            
            # Réinitialiser le cooldown du saut après avoir sauté
            if self.last_action == 'jump':
                self.jump_cooldown = 10  # Augmenté pour espacer davantage les sauts
            
            # Choisir l'action avec le score le plus élevé
            best_action = max(action_scores, key=action_scores.get)
            self.last_action = best_action
            
            # Diminuer graduellement le taux d'exploration, mais plus lentement
            self.exploration_rate = max(self.min_exploration_rate, 
                                    self.exploration_rate * 0.999)
            
            print(f"Action: {best_action}, Scores: {action_scores}")
            return best_action
            
        except Exception as e:
            print(f"ERREUR dans choose_action: {e}")
            # En cas d'erreur, faire un mouvement vers la droite par défaut
            return 'right'  # Changer pour favoriser le mouvement
    
    def handle_menu_action(self):
        """
        Gère les actions spécifiques au menu
        Utilise une séquence spécifique pour naviguer efficacement dans le menu
        """
        # Séquence d'actions pour naviguer dans le menu
        menu_sequence = ['right', 'jump', 'right', 'right', 'jump']
        
        # Incrémenter le compteur et obtenir l'action correspondante
        action = menu_sequence[self.menu_action_counter % len(menu_sequence)]
        self.menu_action_counter += 1
        
        print(f"Action de menu: {action}, compteur: {self.menu_action_counter}")
        return action
    
    def distance(self, pos1, pos2):
        """Calcule la distance euclidienne entre deux points"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5
    
    def train(self, state, action, reward, next_state, done):
        """
        Entraîne l'agent avec une nouvelle expérience
        """
        # Mettre à jour la table Q
        self.update(state, action, reward, next_state, done)
        
        # Si l'épisode est terminé, mettre à jour les statistiques
        if done:
            self.game_count += 1
            
            # Vérifier si c'est une victoire (détection du checkpoint) ou une défaite
            if reward > 50:  # Récompense élevée indique probablement un checkpoint
                self.wins += 1
                print(f"Victoire! Ratio de victoires: {self.wins}/{self.game_count} ({(self.wins/self.game_count)*100:.1f}%)")
            else:
                self.losses += 1
                print(f"Défaite. Ratio de victoires: {self.wins}/{self.game_count} ({(self.wins/self.game_count)*100:.1f}%)")
            
            # Mémoriser les erreurs et ajuster les poids en conséquence
            if reward < 0 and self.last_episode_state is not None and self.last_episode_action is not None:
                # Si la récompense est négative, ajuster les poids pour éviter les mêmes erreurs
                print("Apprentissage à partir d'une erreur...")
                if "jump_over_gap" in self.weights and self.last_episode_action == "jump":
                    self.weights["jump_over_gap"] *= 1.05  # Augmenter légèrement
                elif "forward_progress" in self.weights and self.last_episode_action == "right":
                    self.weights["forward_progress"] *= 0.95  # Diminuer légèrement
                
                print(f"Poids ajustés: {self.weights}")
            
            # Sauvegarder l'état et l'action de cet épisode
            self.last_episode_state = state
            self.last_episode_action = action
        
        # Faire également un apprentissage par experience replay
        if len(self.experience_buffer) > 10:
            # Échantillonner aléatoirement des expériences du tampon
            batch_size = min(10, len(self.experience_buffer))
            batch = random.sample(self.experience_buffer, batch_size)
            
            # Mettre à jour la table Q pour chaque expérience du lot
            for exp_state, exp_action, exp_reward, exp_next_state, exp_done in batch:
                self.update(exp_state, exp_action, exp_reward, exp_next_state, exp_done)
    
    def update(self, state, action, reward, next_state, done):
        """
        Met à jour la mémoire de l'agent en fonction de l'expérience vécue
        """
        # Liste des actions disponibles
        actions = ['left', 'right', 'jump', 'idle']
        
        # Ajouter l'expérience au tampon
        self.experience_buffer.append((state, action, reward, next_state, done))
        if len(self.experience_buffer) > self.max_buffer_size:
            self.experience_buffer.pop(0)
        
        # Mise à jour de la table Q par apprentissage par renforcement
        try:
            # Créer des clés simples pour les états
            if "mario_pos" in state:
                # Simplifier l'état en arrondissant les positions (pour réduire le nombre d'états)
                x_grid = int(state['mario_pos'][0] / 10) * 10  # Grille de 10 pixels
                y_grid = int(state['mario_pos'][1] / 10) * 10  # Grille de 10 pixels
                
                # État actuel
                state_key = f"{x_grid}-{y_grid}"
                
                # État suivant
                if "mario_pos" in next_state:
                    next_x_grid = int(next_state['mario_pos'][0] / 10) * 10
                    next_y_grid = int(next_state['mario_pos'][1] / 10) * 10
                    next_state_key = f"{next_x_grid}-{next_y_grid}"
                else:
                    next_state_key = "terminal"
                
                # Calculer la distance parcourue
                if "mario_pos" in next_state and self.last_position != (0, 0):
                    distance_traveled = next_state["mario_pos"][0] - self.last_position[0]
                    # Ajouter un bonus de récompense pour le progrès en avant
                    if distance_traveled > 0:
                        reward += distance_traveled * 0.01  # Petit bonus proportionnel à la distance
                
                # Mise à jour de la dernière position connue
                if "mario_pos" in next_state:
                    self.last_position = next_state["mario_pos"]
                
                # Stocker les expériences importantes (récompenses élevées ou pénalités)
                if abs(reward) > 5:  # Expérience significative
                    self.previous_experiences[state_key] = (action, reward, done)
                    print(f"Expérience significative mémorisée: état {state_key}, action {action}, récompense {reward}")
                
                # Initialiser les valeurs Q si nécessaire
                if state_key not in self.q_table:
                    self.q_table[state_key] = {a: 0.0 for a in actions}
                if next_state_key != "terminal" and next_state_key not in self.q_table:
                    self.q_table[next_state_key] = {a: 0.0 for a in actions}
                
                # Calculer la valeur Q actuelle
                current_q = self.q_table[state_key].get(action, 0.0)
                
                # Calculer la valeur Q maximale pour l'état suivant
                if next_state_key != "terminal":
                    max_future_q = max(self.q_table[next_state_key].values())
                else:
                    max_future_q = 0.0
                
                # Ajuster le taux d'apprentissage en fonction de l'importance de l'expérience
                adjusted_learning_rate = self.learning_rate
                # Augmenter le taux d'apprentissage pour les expériences importantes (échecs ou succès)
                if abs(reward) > 10:
                    adjusted_learning_rate = min(0.9, self.learning_rate * 2.0)
                    print(f"Expérience importante! Taux d'apprentissage ajusté: {adjusted_learning_rate}")
                
                # Mise à jour de la valeur Q en utilisant la formule de Bellman
                new_q = (1 - adjusted_learning_rate) * current_q + adjusted_learning_rate * (reward + self.discount_factor * max_future_q)
                self.q_table[state_key][action] = new_q
                
                # Mettre à jour les valeurs Q des actions pour des états similaires (généralisation)
                # Cela aide l'agent à appliquer ses apprentissages à des situations similaires
                if "mario_vel" in state and abs(reward) > 5:
                    mario_vel = state["mario_vel"]
                    # Si Mario se déplace vers la droite, trouver des états similaires
                    if mario_vel[0] > 0:
                        for nearby_x in range(x_grid-30, x_grid+40, 10):
                            nearby_state = f"{nearby_x}-{y_grid}"
                            if nearby_state in self.q_table and nearby_state != state_key:
                                # Propager l'apprentissage avec un facteur d'atténuation
                                attenuation = 0.7  # L'impact diminue avec la distance
                                old_q = self.q_table[nearby_state].get(action, 0.0)
                                propagated_q = (1 - adjusted_learning_rate * attenuation) * old_q + adjusted_learning_rate * attenuation * new_q
                                self.q_table[nearby_state][action] = propagated_q
                                print(f"Apprentissage propagé à l'état similaire {nearby_state}")
                
                # Afficher les informations de mise à jour
                print(f"Mise à jour Q: État {state_key}, Action {action}, Récompense {reward:.2f}, Nouvelle valeur Q {new_q:.2f}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la table Q: {e}")
        
        # Sauvegarder la mémoire périodiquement
        if done:
            # Enregistrer la récompense totale de l'épisode
            total_reward = sum(reward for _, _, reward, _, _ in self.experience_buffer[-200:])  # Approximation
            self.episode_rewards.append(total_reward)
            
            # Ajuster les poids en fonction des tendances récentes de réussite/échec
            if len(self.episode_rewards) > 2:
                recent_trend = self.episode_rewards[-1] - self.episode_rewards[-2]
                # Si les récompenses diminuent, ajuster les poids pour encourager plus d'exploration
                if recent_trend < 0:
                    print("Performance en baisse, ajustement des poids...")
                    self.weights["jump_over_gap"] *= 1.05  # Augmenter la priorité des sauts
                    self.weights["forward_progress"] *= 0.95  # Réduire la priorité d'avancer
                    self.exploration_rate = min(0.8, self.exploration_rate * 1.1)  # Augmenter l'exploration
                    print(f"Nouveaux poids: {self.weights}, exploration: {self.exploration_rate:.2f}")
                # Si les récompenses augmentent, renforcer la stratégie actuelle
                elif recent_trend > 10:
                    print("Performance en hausse, renforcement de la stratégie...")
                    self.exploration_rate = max(self.min_exploration_rate, self.exploration_rate * 0.95)
                    print(f"Taux d'exploration réduit à {self.exploration_rate:.2f}")
            
            self.save_memory()
            print("Sauvegarde de la mémoire d'IA après fin d'épisode")
    
    def load_memory(self):
        """
        Charge la mémoire (table Q) depuis un fichier
        """
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.q_table = pickle.load(f)
            print("Mémoire chargée avec succès")
        else:
            print("Aucune mémoire trouvée, utilisation des valeurs par défaut")
            self.q_table = {}
    
    def save_memory(self):
        """
        Sauvegarde la mémoire (table Q) dans un fichier
        """
        with open(self.model_path, "wb") as f:
            pickle.dump(self.q_table, f)
        print("Mémoire sauvegardée avec succès")
    
    def detect_checkpoint(self, screen):
        """
        Détecte la présence d'un checkpoint en comparant l'écran actuel avec l'image du checkpoint
        """
        if self.checkpoint_image is not None:
            # Redimensionner l'image du checkpoint pour qu'elle corresponde à la taille de l'écran
            checkpoint_resized = cv2.resize(self.checkpoint_image, (screen.get_width(), screen.get_height()))
            
            # Convertir l'écran en tableau numpy
            screen_array = pygame.surfarray.array3d(screen)
            
            # Calculer la différence entre l'écran et l'image du checkpoint
            diff = cv2.absdiff(checkpoint_resized, screen_array)
            
            # Convertir en niveaux de gris
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Seuiller l'image pour obtenir un masque binaire
            _, mask = cv2.threshold(diff_gray, 25, 255, cv2.THRESH_BINARY)
            
            # Calculer le pourcentage de pixels différents
            non_zero_count = cv2.countNonZero(mask)
            total_count = mask.size
            difference_ratio = non_zero_count / total_count
            
            print(f"Ratio de différence: {difference_ratio}")
            
            # Si le ratio de différence est faible, on considère que le checkpoint est détecté
            if difference_ratio < 0.05:
                print("Checkpoint détecté")
                return True
        
        return False