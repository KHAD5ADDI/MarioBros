"""
Agent exploratoire pour Super Mario Python.
Cet agent utilise des actions aléatoires pour explorer l'environnement.
"""

import random
import numpy as np

class ExploratoryAgent:
    """
    Agent exploratoire qui utilise des actions aléatoires pour explorer l'environnement.
    Cette classe définit un agent simple qui choisit des actions de manière aléatoire.
    """
    
    def __init__(self, exploration_rate=0.8):
        """
        Initialise l'agent exploratoire.
        
        Args:
            exploration_rate (float): Taux d'exploration, entre 0 et 1.
                Plus cette valeur est élevée, plus l'agent prendra des actions aléatoires.
        """
        self.exploration_rate = exploration_rate
        self.last_action = None
        self.action_counter = 0
        self.max_same_action = 5  # Nombre maximal de fois pour répéter la même action
        self.blocked_positions = []  # Liste des positions où Mario a été bloqué
        self.blocked_radius = 32  # Rayon de tolérance pour détecter un retour sur une zone bloquée

    def is_near_blocked_position(self, mario_pos):
        """Retourne True si Mario est proche d'une position de blocage mémorisée."""
        for pos in self.blocked_positions:
            if np.linalg.norm(np.array(mario_pos) - np.array(pos)) < self.blocked_radius:
                return True
        return False

    def add_blocked_position(self, mario_pos):
        """Ajoute une position de blocage si elle n'est pas déjà mémorisée (avec tolérance)."""
        for pos in self.blocked_positions:
            if np.linalg.norm(np.array(mario_pos) - np.array(pos)) < self.blocked_radius:
                return  # Déjà mémorisée
        self.blocked_positions.append(tuple(mario_pos))

    def choose_action(self, state):
        """
        Choisit une action à effectuer en fonction de l'état actuel.
        - Sauter si un ennemi, un bloc ou un trou est détecté devant Mario ET que Mario est au sol et avance.
        - Sinon, avancer à droite ('right').
        """
        action = 'right'
        mario_pos = state.get("mario_pos", [0, 0]) if isinstance(state, dict) else [0, 0]
        mario_vel = state.get("mario_vel", [0, 0]) if isinstance(state, dict) else [0, 0]
        is_on_ground = mario_vel[1] == 0
        avance = mario_vel[0] > 0
        # Saut automatique si Mario revient sur une zone de blocage
        if self.is_near_blocked_position(mario_pos) and is_on_ground:
            return 'jump'
        if isinstance(state, dict) and "nearby_objects" in state:
            enemy_ahead = False
            block_ahead = False
            ground_ahead = False
            # Analyse des objets proches
            for obj in state["nearby_objects"]:
                rel_x, rel_y, obj_type = obj
                # Ennemi devant
                if obj_type in ["Goomba", "Koopa"] and 0 < rel_x < 60 and abs(rel_y) < 40:
                    enemy_ahead = True
                # Bloc devant
                if ("Block" in obj_type or "Brick" in obj_type or "Tile" in obj_type) and 10 < rel_x < 40 and -40 < rel_y < 5:
                    block_ahead = True
                # Sol devant (pour détecter les trous, fenêtre plus étroite)
                if ("Tile" in obj_type or "Block" in obj_type or "Brick" in obj_type) and 32 < rel_x < 64 and -10 < rel_y < 40:
                    ground_ahead = True
            # Trou détecté si pas de sol devant, Mario avance et est au sol
            trou_ahead = not ground_ahead and avance
            if is_on_ground and avance and (enemy_ahead or block_ahead or trou_ahead):
                return 'jump'
        return action
    
    def train(self, last_state, last_action, reward, state, done, info=None):
        """
        Méthode d'entraînement vide pour compatibilité avec l'interface attendue.
        L'agent exploratoire ne fait pas d'apprentissage.
        
        Entraînement : si Mario meurt par blocage (immobilité), mémorise la position.
        info : dict optionnel contenant des infos sur la mort (ex : 'blocked_death': True)
        """
        if done and info is not None and info.get('blocked_death', False):
            mario_pos = last_state.get("mario_pos", [0, 0]) if isinstance(last_state, dict) else [0, 0]
            self.add_blocked_position(mario_pos)
        pass