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
    
    def choose_action(self, state):
        """
        Choisit une action à effectuer en fonction de l'état actuel.
        Pour l'agent exploratoire, l'action est majoritairement aléatoire,
        avec une tendance à favoriser le mouvement vers la droite.
        
        Args:
            state: L'état actuel du jeu (non utilisé dans cet agent)
            
        Returns:
            str: L'action choisie ('left', 'right', 'jump', ou 'idle')
        """
        # Liste des actions possibles
        actions = ['left', 'right', 'jump', 'idle']
        
        # Favoriser les actions qui font avancer (droite et saut)
        # et éviter de rester bloqué en répétant la même action trop longtemps
        if self.last_action and random.random() > self.exploration_rate:
            # Si on a déjà choisi une action précédemment et qu'on veut exploiter
            if self.action_counter < self.max_same_action:
                # Continuer avec la même action pour un certain temps
                self.action_counter += 1
                return self.last_action
            else:
                # Changer d'action après avoir répété la même action plusieurs fois
                self.action_counter = 0
                
                # Éviter de faire l'inverse de la dernière action
                if self.last_action == 'left':
                    new_action = random.choice(['right', 'jump', 'idle'])
                elif self.last_action == 'right':
                    # Favoriser la continuation vers la droite ou le saut
                    new_action = random.choices(
                        ['right', 'jump', 'idle', 'left'],
                        weights=[0.5, 0.3, 0.1, 0.1]
                    )[0]
                else:
                    new_action = random.choice(actions)
                
                self.last_action = new_action
                return new_action
        
        # Exploration: choisir une action aléatoire
        # Mais avec un biais vers la droite et le saut
        new_action = random.choices(
            actions,
            weights=[0.1, 0.5, 0.3, 0.1]  # Favoriser droite (0.5) et saut (0.3)
        )[0]
        
        self.last_action = new_action
        self.action_counter = 1
        return new_action