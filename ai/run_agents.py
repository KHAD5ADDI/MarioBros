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

def run_ai_mario(agent_type="guided", max_games=None, return_to_menu=True):
    """
    Fonction principale qui exécute Mario avec un agent IA en mode apprentissage continu.
    
    Args:
        agent_type (str): Le type d'agent IA à utiliser ('guided' ou 'exploratory')
        max_games (int): Nombre maximum de parties à jouer (None = illimité)
        return_to_menu (bool): Si True, retourne 'menu_principal' à la fin
        
    Returns:
        str: 'menu_principal' si return_to_menu est True, sinon None
    """
    print(f"Démarrage de Super Mario avec agent {agent_type} en mode apprentissage continu...")
    
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
    
    try:
        # Boucle principale du jeu - continue jusqu'à max_games ou indéfiniment si max_games est None
        while max_games is None or total_games < max_games:
            print(f"\n--- Partie {total_games + 1} ---")
            total_games += 1
            
            # Réinitialiser l'environnement
            state = env.reset()
            done = False
            steps = 0
            total_reward = 0
            last_state = None
            last_action = None
            
            # Naviguer d'abord dans le menu jusqu'au niveau
            print("Navigation dans les menus...")
            menu_actions = ['right', 'jump']  # Actions simplifiées pour le menu
            for action in menu_actions:
                next_state, reward, done, info = env.step(action)
                pygame.time.delay(300)  # Temps d'attente réduit pour accélérer
                state = next_state
            
            # Attendre que le niveau se charge
            pygame.time.delay(1000)  # Temps d'attente réduit pour accélérer
            
            print(f"Début du jeu avec l'agent {agent_type}...")
            # Boucle de jeu principale
            while not done and steps < 5000:  # Limite augmentée pour permettre des niveaux plus longs
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
                
                # Choisir l'action avec l'agent et mettre à jour l'agent avec l'expérience précédente
                if agent:
                    # Entraîner l'agent avec l'expérience précédente
                    if last_state is not None and last_action is not None:
                        agent.train(last_state, last_action, total_reward, state, done)
                    
                    # Choisir la prochaine action
                    action = agent.choose_action(state)
                else:
                    # Mode test: actions aléatoires
                    action = env.actions[random.randint(0, len(env.actions)-1)]
                
                # Sauvegarder l'état et l'action actuels
                last_state = state
                last_action = action
                
                # Exécuter l'action dans l'environnement
                next_state, reward, done, info = env.step(action)
                total_reward += reward
                
                # Mettre à jour l'état pour la prochaine itération
                state = next_state
                steps += 1
                
                # Ralentir un peu pour que le jeu soit visible mais pas trop lent
                pygame.time.delay(5)  # Délai minimal pour permettre un apprentissage rapide
                
                # Afficher des statistiques moins fréquemment pour optimiser les performances
                if steps % 200 == 0:
                    print(f"Étapes: {steps}, Récompense totale: {total_reward:.2f}")
            
            # Fin de partie - s'assurer que l'agent apprend aussi de la dernière expérience
            if agent and last_state is not None and last_action is not None:
                # Une grande récompense négative si Mario est mort, positive s'il a atteint le checkpoint
                if info["game_state"] == "checkpoint_reached":
                    final_reward = 1000
                elif info["game_state"] == "game_over":
                    final_reward = -100
                else:
                    final_reward = 0
                
                agent.train(last_state, last_action, final_reward, state, done)
            
            # Afficher les statistiques de la partie
            if done:
                result_message = "Checkpoint atteint!" if info["game_state"] == "checkpoint_reached" else "Mario est mort"
                print(f"Partie terminée! {result_message}")
                print(f"Statistiques: {steps} étapes, {total_reward:.2f} points")
                
                # Message temporaire à l'écran indiquant la prochaine partie
                font = pygame.font.Font(None, 36)
                text = font.render(f"Partie {total_games} terminée, prochaine partie...", True, (255, 255, 255))
                env.screen.fill((0, 0, 0))
                env.screen.blit(text, (100, 200))
                pygame.display.update()
                
                # Vérifier si l'utilisateur veut quitter
                for i in range(30):  # 3 secondes pour permettre à l'utilisateur d'annuler
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            env.close()
                            return 'menu_principal' if return_to_menu else None
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                env.close()
                                return 'menu_principal' if return_to_menu else None
                    pygame.time.delay(100)
            
    except KeyboardInterrupt:
        print("Apprentissage interrompu par l'utilisateur")
    finally:
        # Fermer l'environnement proprement
        env.close()
        print(f"Apprentissage terminé après {total_games} parties.")
    
    return 'menu_principal' if return_to_menu else None