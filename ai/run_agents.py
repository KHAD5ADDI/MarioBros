"""
Module contenant les fonctions pour exécuter les agents IA avec Mario.
Ce module centralise le code pour éviter la duplication entre main.py et main_ai.py.
"""

import sys
import pygame
import random
import time
import os
import numpy as np
from ai.mario_env import MarioEnv
from ai.agents.GuidedAgent import GuidedAgent
from ai.agents.ExploratoryAgent import ExploratoryAgent
from utils import suppress_pygame_warnings

def run_ai_mario(agent_type="guided", max_games=10, return_to_menu=True):
    """
    Fonction principale qui exécute Mario avec un agent IA.
    
    Args:
        agent_type (str): Le type d'agent IA à utiliser ('guided' ou 'exploratory')
        max_games (int): Nombre maximum de parties à jouer
        return_to_menu (bool): Si True, retourne 'menu_principal' à la fin
        
    Returns:
        str: 'menu_principal' si return_to_menu est True, sinon None
    """
    print(f"Démarrage de Super Mario avec agent {agent_type}...")
    
    # Supprimer les avertissements libpng
    stderr_redirect = suppress_pygame_warnings()
    
    # Utiliser le gestionnaire de contexte pour supprimer les avertissements
    with stderr_redirect():
        # Créer l'environnement
        env = MarioEnv(agent_type=agent_type)
    
    # Créer l'agent selon le type choisi
    if agent_type == "guided":
        agent = GuidedAgent()
    elif agent_type == "exploratory":
        agent = ExploratoryAgent()
    else:  # Mode test ou autre
        agent = None
    
    # Variables pour suivre l'état du jeu
    total_games = 0
    
    # Boucle principale du jeu
    while total_games < max_games:
        print(f"\n--- Partie {total_games + 1} ---")
        total_games += 1
        
        # Réinitialiser l'environnement
        state = env.reset()
        done = False
        steps = 0
        total_reward = 0
        
        # Naviguer d'abord dans le menu jusqu'au niveau
        print("Navigation dans les menus...")
        # Forcer certaines actions pour naviguer à travers le menu
        menu_actions = ['right', 'right', 'jump', 'jump']
        for action in menu_actions:
            next_state, reward, done, info = env.step(action)
            pygame.time.delay(500)  # Attendre pour voir les actions se dérouler
            state = next_state
        
        # Attendre que le niveau se charge complètement
        print("Chargement du niveau en cours...")
        pygame.time.delay(2000)  # Attendre 2 secondes pour que le niveau se charge
        
        # Afficher un message sur l'écran indiquant que le jeu va commencer
        font = pygame.font.Font(None, 36)
        text = font.render("Prêt? Le jeu commence dans...", True, (255, 255, 255))
        env.screen.blit(text, (160, 200))
        pygame.display.update()
        
        # Compte à rebours avant de commencer
        for i in range(3, 0, -1):
            # Effacer l'écran
            env.screen.fill((104, 136, 252))
            text = font.render(f"{i}...", True, (255, 255, 255))
            env.screen.blit(text, (310, 200))
            pygame.display.update()
            pygame.time.delay(1000)  # 1 seconde entre chaque chiffre
        
        print(f"Début du jeu avec l'agent {agent_type}...")
        # Boucle de jeu principale
        while not done and steps < 2000:  # Limite de pas pour éviter les boucles infinies
            # Gérer les événements pygame pour éviter de bloquer l'interface
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        print("Jeu interrompu par l'utilisateur")
                        env.close()
                        return 'menu_principal' if return_to_menu else None
            
            # Choisir l'action avec l'agent ou aléatoirement
            if agent:
                action = agent.choose_action(state)
            else:
                # Mode test: actions aléatoires
                action = env.actions[random.randint(0, len(env.actions)-1)]
            
            # Exécuter l'action dans l'environnement
            next_state, reward, done, info = env.step(action)
            total_reward += reward
            
            # Mettre à jour l'état pour la prochaine itération
            state = next_state
            steps += 1
            
            # Ralentir un peu pour que le jeu soit visible
            pygame.time.delay(10)
            
            # Afficher des statistiques toutes les 100 étapes
            if steps % 100 == 0:
                print(f"Étapes: {steps}, Récompense totale: {total_reward:.2f}")
        
        # Fin de partie
        if done:
            if hasattr(state, "get") and "mario_pos" in state and state["mario_pos"][1] > 450:
                print(f"Mario est tombé dans un trou! Récompense: {total_reward:.2f}")
            else:
                print(f"Partie terminée! Récompense totale: {total_reward:.2f}")
            
            # Afficher un message à l'écran
            font = pygame.font.Font(None, 36)
            text1 = font.render("Partie terminée!", True, (255, 255, 255))
            text2 = font.render("Appuyez sur ESPACE pour continuer, ESC pour quitter", True, (255, 255, 255))
            env.screen.blit(text1, (200, 200))
            env.screen.blit(text2, (50, 250))
            pygame.display.update()
            
            # Attendre l'action de l'utilisateur
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            waiting = False  # Continuer à la prochaine partie
                        elif event.key == pygame.K_ESCAPE:
                            env.close()
                            return 'menu_principal' if return_to_menu else None
                pygame.time.delay(100)
        
        # Attendre un peu avant de commencer une nouvelle partie
        pygame.time.delay(2000)
    
    # Fermer l'environnement
    env.close()
    print("Toutes les parties terminées.")
    return 'menu_principal' if return_to_menu else None