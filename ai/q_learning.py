# q_learning.py

import numpy as np
import pygame
from ai.mario_env import MarioEnv

# Créer l'environnement
agent_type = "exploratory"  # "guided" ou "exploratory"
env = MarioEnv(agent_type=agent_type)

# Configuration de l'algorithme Q-learning
def get_state_key(state):
    """Convertit un état numpy en clé hashable pour la table Q"""
    if isinstance(state, dict):  # Pour l'agent guidé
        # Simplifions l'état pour le rendre hashable
        mario_pos = tuple(map(int, state["mario_pos"]))
        mario_vel = tuple(map(lambda x: int(x*10), state["mario_vel"]))  # Arrondir les vitesses
        return (mario_pos, mario_vel, state["mario_size"])
    else:  # Pour l'agent exploratoire
        # Discrétiser l'état pour éviter d'avoir trop de valeurs différentes
        return tuple(state.astype(int))

# Initialisation de la table Q
q_table = {}  # Dictionnaire pour stocker les valeurs Q

# Hyperparamètres
alpha = 0.1  # Taux d'apprentissage
gamma = 0.99  # Facteur de discount
epsilon = 0.3  # Taux d'exploration

# Afficher les infos de l'épisode
episode_rewards = []
best_reward = -float('inf')

# Boucle d'entraînement
n_episodes = 500
for episode in range(n_episodes):
    state = env.reset()
    state_key = get_state_key(state)
    done = False
    episode_reward = 0
    
    step_count = 0
    max_steps = 1000  # Nombre maximum d'étapes par épisode
    
    # Gérer l'événement de fermeture (croix de la fenêtre)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    
    while not done and step_count < max_steps:
        # Politique epsilon-greedy
        if np.random.rand() < epsilon:
            action_idx = np.random.choice(len(env.actions))
            action = env.actions[action_idx]
        else:
            # Choisir la meilleure action selon la table Q
            q_values = [q_table.get((state_key, a), 0) for a in env.actions]
            action_idx = np.argmax(q_values)
            action = env.actions[action_idx]
        
        # Exécuter l'action
        next_state, reward, done, _ = env.step(action)
        next_state_key = get_state_key(next_state)
        episode_reward += reward
        
        # Mettre à jour la table Q
        old_value = q_table.get((state_key, action), 0)
        next_max = max([q_table.get((next_state_key, a), 0) for a in env.actions])
        
        new_value = old_value + alpha * (reward + gamma * next_max - old_value)
        q_table[(state_key, action)] = new_value
        
        state_key = next_state_key
        step_count += 1
    
    # Réduire epsilon (exploration) au fil du temps
    epsilon = max(0.1, epsilon * 0.995)
    
    # Enregistrer les performances
    episode_rewards.append(episode_reward)
    if episode_reward > best_reward:
        best_reward = episode_reward
    
    # Afficher les stats tous les 10 épisodes
    if episode % 10 == 0:
        avg_reward = np.mean(episode_rewards[-10:])
        print(f"Épisode {episode}/{n_episodes}, Récompense: {episode_reward:.2f}, Moyenne: {avg_reward:.2f}, Meilleure: {best_reward:.2f}, Epsilon: {epsilon:.3f}")

print("Entraînement terminé!")
env.close()

# On peut sauvegarder la table Q pour la réutiliser plus tard
import pickle
with open(f"q_table_{agent_type}.pkl", "wb") as f:
    pickle.dump(q_table, f)