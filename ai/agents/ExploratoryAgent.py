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
        avec une tendance à favoriser le mouvement vers la droite et les sauts.
        
        Args:
            state: L'état actuel du jeu (non utilisé dans cet agent)
            
        Returns:
            str: L'action choisie ('left', 'right', 'jump', ou 'idle')
        """
        # Liste des actions possibles
        actions = ['left', 'right', 'jump', 'idle']
        
        # Ajouter un facteur de saut aléatoire (30% de chances de sauter à tout moment)
        if random.random() < 0.3:
            self.last_action = 'jump'
            self.action_counter = 1
            return 'jump'
        
        # Favoriser les actions qui font avancer (droite et saut)
        # et éviter de rester bloqué en répétant la même action trop longtemps
        if self.last_action and random.random() > self.exploration_rate:
            # Si on a déjà choisi une action précédemment et qu'on veut exploiter
            if self.action_counter < self.max_same_action:
                # Continuer avec la même action pour un certain temps
                self.action_counter += 1
                # Ajouter une chance de sauter pendant qu'on avance vers la droite
                if self.last_action == 'right' and random.random() < 0.25:
                    return 'jump'
                return self.last_action
            else:
                # Changer d'action après avoir répété la même action plusieurs fois
                self.action_counter = 0
                
                # Éviter de faire l'inverse de la dernière action
                if self.last_action == 'left':
                    new_action = random.choice(['right', 'jump', 'jump', 'idle'])  # Favorise le saut
                elif self.last_action == 'right':
                    # Favoriser la continuation vers la droite ou le saut (davantage de sauts)
                    new_action = random.choices(
                        ['right', 'jump', 'idle', 'left'],
                        weights=[0.4, 0.5, 0.05, 0.05]  # Priorité au saut
                    )[0]
                else:
                    new_action = random.choices(
                        actions,
                        weights=[0.1, 0.4, 0.4, 0.1]  # Favoriser également droite et saut
                    )[0]
                
                self.last_action = new_action
                return new_action
        
        # Exploration: choisir une action aléatoire
        # Mais avec un biais fort vers la droite et le saut
        new_action = random.choices(
            actions,
            weights=[0.05, 0.45, 0.45, 0.05]  # Équilibre entre droite et saut (0.45 chacun)
        )[0]
        
        self.last_action = new_action
        self.action_counter = 1
        return new_action