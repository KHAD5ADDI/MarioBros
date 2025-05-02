# GuidedAgent.py

import numpy as np
import random
import pygame

class GuidedAgent:
    """
    Agent guidé pour Super Mario Python
    
    Cet agent utilise des informations structurées sur l'environnement
    pour prendre des décisions plus informées.
    """
    
    def __init__(self):
        # Paramètres de l'agent
        self.exploration_rate = 0.3  # Taux d'exploration initial
        self.min_exploration_rate = 0.05  # Taux minimal d'exploration
        self.exploration_decay = 0.995  # Taux de décroissance de l'exploration
        
        # Initialiser les poids pour différentes caractéristiques
        self.weights = {
            "distance_to_enemy": -2.0,  # Pénalité pour être proche d'un ennemi
            "distance_to_coin": 1.0,    # Récompense pour être proche d'une pièce
            "forward_progress": 4.0,    # Préférence pour avancer (augmenté)
            "jump_over_gap": 2.5,       # Récompense pour sauter par-dessus un trou
            "jump_over_enemy": 3.0,     # Récompense pour sauter par-dessus un ennemi
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
        self.alternating_actions = ['right', 'jump', 'right', 'right']
        self.alternating_index = 0
        
    def choose_action(self, state):
        """
        Sélectionne une action en fonction de l'état actuel
        """
        try:
            # Actions possibles
            actions = ['left', 'right', 'jump', 'idle']
            
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
                action = random.choice(['right', 'jump', 'right'])  # Favoriser droite et saut
                print(f"Action aléatoire: {action}")
                return action
            
            # Gérer les événements pygame
            pygame.event.pump()
            
            # Récupérer les informations d'état
            mario_pos = state["mario_pos"]
            mario_vel = state["mario_vel"]
            nearby_objects = state["nearby_objects"]
            
            # Afficher des informations de débogage (réduites)
            print(f"Position: {mario_pos}, Vitesse: {mario_vel}, Objets: {len(nearby_objects)}")
            
            # Calculer les scores pour chaque action
            action_scores = {
                'left': 0,
                'right': self.weights["forward_progress"],  # Préférer aller à droite
                'jump': 0,
                'idle': 0
            }
            
            # Réduire le cooldown du saut
            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
                action_scores['jump'] -= 2.0  # Pénalité pour sauter trop fréquemment
            
            # Détecter les ennemis à l'avant
            enemies_ahead = False
            enemies_close = False
            
            # Analyser les objets proches
            ground_tiles_ahead = []
            ground_tiles_below = []
            coins_above = False
            
            for obj in nearby_objects:
                rel_x, rel_y, obj_type = obj
                
                # Détecter les ennemis
                if "Goomba" in obj_type or "Koopa" in obj_type:
                    if 0 < rel_x < 80 and abs(rel_y) < 50:  # Ennemi à droite proche
                        enemies_ahead = True
                        if rel_x < 40:  # Très proche
                            enemies_close = True
                            action_scores['jump'] += self.weights["jump_over_enemy"] * 1.5
                            print("Ennemi très proche, je saute!")
                        else:
                            action_scores['jump'] += self.weights["jump_over_enemy"]
                            print("Ennemi détecté devant, je saute!")
                
                # Détecter les objets à collecter
                if any(item in obj_type for item in ["Coin", "CoinBox", "RandomBox", "Mushroom"]):
                    # Item au-dessus de Mario
                    if abs(rel_x) < 16 and -150 < rel_y < -20:
                        coins_above = True
                        action_scores['jump'] += self.weights["distance_to_coin"]
                        print("Bonus au-dessus, je saute!")
                    # Item devant Mario
                    elif 0 < rel_x < 100:
                        action_scores['right'] += self.weights["distance_to_coin"] * 0.5
                
                # Identifier les tuiles du sol
                if "Tile" in obj_type:
                    # Tuiles directement sous Mario
                    if abs(rel_x) < 16 and 0 < rel_y < 32:
                        ground_tiles_below.append(obj)
                    # Tuiles devant Mario (pour détecter les trous)
                    elif 16 < rel_x < 96 and -10 < rel_y < 40:
                        ground_tiles_ahead.append(obj)
            
            # Vérifier s'il y a un sol devant (sinon, c'est un trou)
            if len(ground_tiles_ahead) == 0 and mario_vel[0] >= 0:
                # Pas de sol détecté devant = probablement un trou
                action_scores['jump'] += self.weights["jump_over_gap"] * 2
                print("Trou détecté, je saute!")
            
            # Si on est en l'air, continuer à avancer
            if len(ground_tiles_below) == 0 and mario_vel[1] != 0:
                action_scores['right'] += 1.0  # Continuer sur l'élan
                action_scores['jump'] -= 2.0  # Éviter de sauter à nouveau en l'air
            
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
                
                if self.stuck_counter > 15:
                    print("Je semble bloqué, je vais essayer autre chose!")
                    # Alterner entre différentes actions
                    self.force_alternate = True
                    self.alternating_index = 0
                    self.stuck_counter = 0
                    return self.alternating_actions[0]
            else:
                self.stuck_counter = max(0, self.stuck_counter - 1)
            
            # Biais pour aller à droite après avoir sauté
            if self.last_action == 'jump':
                action_scores['right'] += 2.0
                self.right_bias_counter = 5
            
            if self.right_bias_counter > 0:
                action_scores['right'] += 1.0
                self.right_bias_counter -= 1
            
            # Éviter de sauter trop fréquemment
            if self.last_action == 'jump' and self.jump_cooldown <= 0:
                self.jump_cooldown = 8  # Attendre quelques frames avant de sauter à nouveau
            
            # Si on va à droite trop longtemps sans sauter, essayer de sauter occasionnellement
            if self.last_action == 'right':
                self.consecutive_same_actions += 1
                if self.consecutive_same_actions > 40 and not enemies_ahead:
                    action_scores['jump'] += 2.0
                    print("Avancé longtemps sans sauter, je tente un saut exploratoire")
            else:
                self.consecutive_same_actions = 0
            
            # Choisir l'action avec le score le plus élevé
            best_action = max(action_scores, key=action_scores.get)
            self.last_action = best_action
            
            # Diminuer graduellement le taux d'exploration
            self.exploration_rate = max(self.min_exploration_rate, 
                                    self.exploration_rate * self.exploration_decay)
            
            print(f"Action: {best_action}, Scores: {action_scores}")
            return best_action
            
        except Exception as e:
            print(f"ERREUR dans choose_action: {e}")
            # En cas d'erreur, simplement avancer à droite
            return 'right'
    
    def distance(self, pos1, pos2):
        """Calcule la distance euclidienne entre deux points"""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5
    
    def train(self, state, action, reward, next_state, done):
        # Cette méthode pourrait être implémentée plus tard pour un apprentissage plus avancé
        pass