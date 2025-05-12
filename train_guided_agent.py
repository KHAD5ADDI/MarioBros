from ai.mario_env import MarioEnv
from ai.agents.GuidedAgent import GuidedAgent
import pygame
import numpy as np
import sys
import time

def train_guided_agent(num_episodes=10):
    """Fonction principale pour exécuter l'agent guidé sur plusieurs épisodes
    
    Args:
        num_episodes: nombre d'épisodes (parties) à jouer
    """
    print(f"Démarrage de l'agent guidé pour {num_episodes} épisodes...")
    
    try:
        # Initialiser pygame (si ce n'est pas déjà fait)
        if not pygame.get_init():
            pygame.init()
        
        # Créer l'agent guidé (une seule fois pour conserver la mémoire entre les parties)
        agent = GuidedAgent()
        
        # Statistiques globales
        best_score = -float('inf')
        best_distance = 0
        episode_scores = []
        
        # Boucle des épisodes
        for episode in range(1, num_episodes + 1):
            print(f"=== Début de l'épisode {episode}/{num_episodes} ===")
            
            # Créer l'environnement pour cet épisode
            env = MarioEnv(agent_type="guided")
            
            # Paramètres d'exécution
            max_steps = 5000
            
            # Réinitialiser l'environnement
            state = env.reset()
            score = 0
            done = False
            steps = 0
            
            # Vérifier si mario est disponible dans l'état retourné
            if "mario_pos" in state:
                start_x = state["mario_pos"][0]
                print(f"Position initiale de Mario: {state['mario_pos'][0]}, {state['mario_pos'][1]}")
            else:
                start_x = 0
                print("Impossible de détecter la position initiale de Mario")
                
            # Ajouter un attribut pour suivre les pièces collectées si nécessaire
            if hasattr(env, 'dashboard'):
                env.dashboard.coins_collected_last_step = env.dashboard.coins
            
            print(f"Épisode {episode}: Mario prêt à jouer...")
            
            # Pour permettre à l'utilisateur de voir Mario avant de commencer
            time.sleep(0.5)
            
            # Boucle principale de l'épisode
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
                
                # Entraîner l'agent avec cette nouvelle expérience
                agent.train(state, action, reward, next_state, done)
                
                # Mettre à jour l'état et les statistiques
                state = next_state
                score += reward
                steps += 1
                
                # Afficher des informations de progression
                if steps % 200 == 0:
                    current_x = state.get("mario_pos", [0, 0])[0] if "mario_pos" in state else 0
                    distance_traveled = current_x - start_x
                    print(f"Étapes: {steps}, Score: {score:.2f}, Distance parcourue: {distance_traveled}")
                
                # Petite pause pour que l'humain puisse suivre l'action
                time.sleep(0.01)  # Vitesse légèrement accélérée pour les entraînements multiples
            
            # Calculer la distance parcourue
            final_x = state.get("mario_pos", [0, 0])[0] if "mario_pos" in state else 0
            distance_traveled = final_x - start_x
            
            # Mettre à jour les statistiques
            episode_scores.append(score)
            if score > best_score:
                best_score = score
            if distance_traveled > best_distance:
                best_distance = distance_traveled
            
            # Afficher les résultats de l'épisode
            print(f"Fin de l'épisode {episode}! Étapes: {steps}, Score: {score:.2f}")
            print(f"Distance parcourue: {distance_traveled}")
            
            if "mario_pos" in state:
                print(f"Position finale de Mario: X={state['mario_pos'][0]}, Y={state['mario_pos'][1]}")
            
            # Forcer la sauvegarde de la mémoire à la fin de chaque épisode
            agent.save_memory()
            
            # Brève pause entre les épisodes
            time.sleep(1)
            
            # Fermer l'environnement
            env.close()
        
        # Afficher les statistiques globales
        print("\n=== Résultats de l'entraînement ===")
        print(f"Nombre d'épisodes joués: {num_episodes}")
        print(f"Meilleur score: {best_score:.2f}")
        print(f"Meilleure distance parcourue: {best_distance}")
        
        if episode_scores:
            avg_score = sum(episode_scores) / len(episode_scores)
            print(f"Score moyen: {avg_score:.2f}")
        
        # Afficher si l'agent s'est amélioré
        if len(episode_scores) > 1:
            first_half = episode_scores[:len(episode_scores)//2]
            second_half = episode_scores[len(episode_scores)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg > first_avg:
                improvement = ((second_avg - first_avg) / first_avg) * 100
                print(f"Amélioration de l'agent: +{improvement:.2f}% en score moyen")
            else:
                print("L'agent n'a pas montré d'amélioration significative dans cette session")
        
    except Exception as e:
        print(f"ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        # Si une exception se produit, essayer de fermer proprement pygame
        pygame.quit()

if __name__ == "__main__":
    # Si des arguments sont fournis, utiliser le premier comme nombre d'épisodes
    if len(sys.argv) > 1:
        try:
            num_episodes = int(sys.argv[1])
            train_guided_agent(num_episodes)
        except ValueError:
            print(f"Argument invalide: {sys.argv[1]}. Utilisation du nombre d'épisodes par défaut.")
            train_guided_agent()
    else:
        train_guided_agent()