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
import csv
import datetime
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
    total_scores = []
    total_success = 0
    total_episodes = 0
    
    # Initialisation du fichier CSV pour les scores
    csv_path = "scores_mario.csv"
    write_header = not os.path.exists(csv_path)
    
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
        
        # Séquence de navigation dans le menu pour sélectionner le NIVEAU 1
        # Étape 1: Naviguer jusqu'à "Choose Level"
        print("Navigation dans les menus...")
        
        # Attendre un peu pour s'assurer que le menu est chargé
        pygame.time.delay(500)
        
        # Étape 2: Sélectionner "Choose Level" (première option)
        env.step('select')
        pygame.time.delay(300)
        
        # Étape 3: Sélectionner le premier niveau (déjà sélectionné par défaut)
        env.step('select')
        pygame.time.delay(1000)  # Attendre que le niveau se charge
        
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
                    # Correction : GuidedAgent.train attend 5 arguments, ExploratoryAgent 6
                    if hasattr(agent, 'train') and agent.__class__.__name__ == 'GuidedAgent':
                        agent.train(last_state, last_action, total_reward, state, done)
                    else:
                        agent.train(last_state, last_action, total_reward, state, done, info)
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
            # Correction : calculer final_reward avant d'appeler agent.train
            if info["game_state"] == "checkpoint_reached":
                final_reward = 1000
            elif info["game_state"] == "game_over":
                final_reward = -100
            else:
                final_reward = 0
            if agent.__class__.__name__ == 'GuidedAgent':
                agent.train(last_state, last_action, final_reward, state, done)
            else:
                agent.train(last_state, last_action, final_reward, state, done, info)
        # Afficher les statistiques de la partie
        if done:
            result_message = "Checkpoint atteint!" if info["game_state"] == "checkpoint_reached" else "Mario est mort"
            print("\n==============================")
            print(f"Partie terminée! {result_message}")
            print(f"Statistiques: {steps} étapes, {total_reward:.2f} points")
            # --- SCORE SPÉCIFIQUE ---
            if info["game_state"] == "checkpoint_reached":
                # Score = temps pris pour finir (moins c'est mieux)
                if isinstance(state, dict) and "time" in state:
                    score = state["time"]
                    print(f"Score FINAL : TEMPS pour finir le niveau = {score} secondes")
                else:
                    print("Score (temps) non disponible.")
            else:
                # Score = distance parcourue
                if isinstance(state, dict) and "mario_pos" in state:
                    distance = state["mario_pos"][0]
                    print(f"Score FINAL : DISTANCE parcourue = {distance} pixels")
                else:
                    print("Score (distance) non disponible.")
            # --- SUIVI GLOBAL ---
            total_scores.append(total_reward)
            total_episodes += 1
            if info["game_state"] == "checkpoint_reached":
                total_success += 1
            moyenne = sum(total_scores) / len(total_scores)
            taux_reussite = (total_success / total_episodes) * 100
            print(f"Score cumulé (reward total) de l'épisode : {total_reward:.2f}")
            print(f"Score moyen sur {total_episodes} parties : {moyenne:.2f}")
            print(f"Taux de réussite (checkpoint atteint) : {taux_reussite:.1f}%")
            print("==============================\n")
            
            # --- ENREGISTREMENT CSV ---
            # On stocke : épisode, score cumulé, score spécifique, type (distance/temps), réussite
            if info["game_state"] == "checkpoint_reached":
                score_type = "temps"
                score_value = state["time"] if isinstance(state, dict) and "time" in state else None
                success = 1
            else:
                score_type = "distance"
                score_value = state["mario_pos"][0] if isinstance(state, dict) and "mario_pos" in state else None
                success = 0
            with open(csv_path, mode="a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                if write_header:
                    writer.writerow(["episode", "score_cumule", "score_specifique", "type_score", "reussite", "datetime"])
                    write_header = False
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    total_episodes,           # numéro d'épisode
                    total_reward,             # score cumulé
                    score_value,              # score spécifique (distance ou temps)
                    score_type,               # type de score
                    success,                  # réussite (1=checkpoint, 0=non)
                    now                       # date et heure
                ])
            
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
        env.close()
        return 'menu_principal' if return_to_menu else None