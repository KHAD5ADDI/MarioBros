# train_ai.py

import numpy as np
import time
from ai.mario_env import MarioEnv  # L'environnement que tu as créé

env = MarioEnv()
episodes = 10  # Nombre d’épisodes à jouer
epsilon = 0.2  # Exploration vs exploitation
actions = env.actions

# Table Q simplifiée (pas optimale pour un vrai entraînement)
q_table = {}

def get_state_key(state):
    return tuple(np.round(state, 1))  # Arrondi pour réduire l'espace d'état

for episode in range(episodes):
    state = env.reset()
    state_key = get_state_key(state)
    done = False
    total_reward = 0
    print(f"🔁 Episode {episode + 1}")

    while not done:
        # Choisir l'action
        if np.random.rand() < epsilon:
            action = np.random.choice(actions)
        else:
            q_vals = [q_table.get((state_key, a), 0) for a in actions]
            action = actions[np.argmax(q_vals)]

        # Exécuter l’action
        next_state, reward, done, _ = env.step(action)
        env.render()  # Affiche le jeu à chaque frame
        time.sleep(0.02)  # Pour ralentir et rendre visible

        next_state_key = get_state_key(next_state)

        # Q-learning (simplifié)
        old_val = q_table.get((state_key, action), 0)
        next_max = max([q_table.get((next_state_key, a), 0) for a in actions], default=0)

        new_val = old_val + 0.1 * (reward + 0.95 * next_max - old_val)
        q_table[(state_key, action)] = new_val

        state_key = next_state_key
        total_reward += reward

    print(f"🏁 Episode terminé avec récompense totale : {total_reward:.2f}")

env.close()