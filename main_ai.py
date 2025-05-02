# main_ai.py

import numpy as np
from ai.mario_env import MarioEnv

env = MarioEnv()
state = env.reset()
done = False

while not done:
    # Choisir une action (par exemple, aléatoire pour commencer)
    action = np.random.choice(env.actions)
    next_state, reward, done, info = env.step(action)
    state = next_state

env.close()