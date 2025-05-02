from ai.mario_env import MarioEnv
from ai.agents.GuidedAgent import GuidedAgent
import pygame
import numpy as np
import sys
import time

def train_guided_agent():
    """Fonction principale pour exécuter l'agent guidé"""
    print("Démarrage de l'agent guidé...")
    
    try:
        # Initialiser pygame (si ce n'est pas déjà fait)
        if not pygame.get_init():
            pygame.init()
        
        # Créer l'environnement avec l'agent guidé
        env = MarioEnv(agent_type="guided")
        agent = GuidedAgent()
        
        # Paramètres d'exécution
        max_steps = 5000
        
        # Réinitialiser l'environnement
        state = env.reset()
        score = 0
        done = False
        steps = 0
        
        # Ajouter un attribut pour suivre les pièces collectées
        env.dashboard.coins_collected_last_step = env.dashboard.coins
        
        print("Agent guidé prêt à jouer...")
        print("Position initiale de Mario:", env.mario.rect.x, env.mario.rect.y)
        
        # Pour permettre à l'utilisateur de voir Mario avant de commencer
        time.sleep(1)
        
        # Boucle principale
        while not done and steps < max_steps:
            # Gérer les événements Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    env.close()
                    print("Fermeture de l'application")
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        env.close()
                        print("Fermeture de l'application (touche échap)")
                        return
            
            # Obtenir l'action de l'agent
            action = agent.choose_action(state)
            
            # Exécuter l'action dans l'environnement
            next_state, reward, done, info = env.step(action)
            
            # Mettre à jour l'état et les statistiques
            state = next_state
            score += reward
            steps += 1
            
            # Afficher des informations de progression
            if steps % 100 == 0:
                print(f"Étapes: {steps}, Score: {score:.2f}, Position X: {env.mario.rect.x}")
            
            # Petite pause pour que l'humain puisse suivre l'action
            time.sleep(0.02)  # Réduit la vitesse pour mieux voir l'action
        
        # Afficher les résultats finaux
        print(f"Fin de la partie! Étapes: {steps}, Score final: {score:.2f}")
        print(f"Position finale de Mario: X={env.mario.rect.x}, Y={env.mario.rect.y}")
        
        # Maintenir la fenêtre ouverte un moment pour voir le résultat final
        time.sleep(2)
        
        # Fermer l'environnement
        env.close()
        
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        # Si une exception se produit, essayer de fermer proprement pygame
        pygame.quit()

if __name__ == "__main__":
    train_guided_agent()