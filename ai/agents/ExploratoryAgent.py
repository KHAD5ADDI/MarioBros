"""
Agent exploratoire pour Super Mario Python.
Cet agent utilise des actions aléatoires pour explorer l'environnement.
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque

class DQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )
    def forward(self, x):
        return self.net(x)

class ExploratoryAgent:
    """
    Agent exploratoire qui utilise des actions aléatoires pour explorer l'environnement.
    Cette classe définit un agent simple qui choisit des actions de manière aléatoire.
    """
    
    def __init__(self, exploration_rate=0.8, state_dim=8, action_list=None):
        """
        Initialise l'agent exploratoire.
        
        Args:
            exploration_rate (float): Taux d'exploration, entre 0 et 1.
                Plus cette valeur est élevée, plus l'agent prendra des actions aléatoires.
        """
        self.exploration_rate = exploration_rate
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        self.gamma = 0.99
        self.lr = 1e-3
        self.batch_size = 32
        self.memory = deque(maxlen=5000)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.state_dim = state_dim
        self.action_list = action_list if action_list else ['left', 'right', 'jump', 'idle']
        self.action_dim = len(self.action_list)
        self.policy_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.lr)
        self.update_target_steps = 200
        self.learn_step = 0
        self.last_action = None
        self.blocked_positions = []
        self.blocked_radius = 32

    def preprocess_state(self, state):
        # Simplification: concatène position, vitesse, taille, etc. (adapter selon l'observation réelle)
        if isinstance(state, dict):
            mario_pos = state.get("mario_pos", [0, 0])
            mario_vel = state.get("mario_vel", [0, 0])
            mario_size = [state.get("mario_size", 0)]
            # Optionnel: nombre d'ennemis proches, nombre de pièces, etc.
            features = mario_pos + mario_vel + mario_size
            # Compléter à state_dim si besoin
            features += [0] * (self.state_dim - len(features))
            return torch.tensor(features, dtype=torch.float32, device=self.device)
        else:
            # Si déjà un vecteur numpy
            arr = state if hasattr(state, 'tolist') else [0]*self.state_dim
            return torch.tensor(arr[:self.state_dim], dtype=torch.float32, device=self.device)

    def is_near_blocked_position(self, mario_pos):
        """Retourne True si Mario est proche d'une position de blocage mémorisée."""
        for pos in self.blocked_positions:
            if np.linalg.norm(np.array(mario_pos) - np.array(pos)) < self.blocked_radius:
                return True
        return False

    def add_blocked_position(self, mario_pos):
        """Ajoute une position de blocage si elle n'est pas déjà mémorisée (avec tolérance)."""
        for pos in self.blocked_positions:
            if np.linalg.norm(np.array(mario_pos) - np.array(pos)) < self.blocked_radius:
                return  # Déjà mémorisée
        self.blocked_positions.append(tuple(mario_pos))

    def choose_action(self, state):
        state_tensor = self.preprocess_state(state).unsqueeze(0)
        if torch.rand(1).item() < self.exploration_rate:
            action_idx = torch.randint(0, self.action_dim, (1,)).item()
        else:
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
                action_idx = q_values.argmax().item()
        return self.action_list[action_idx]

    def remember(self, state, action, reward, next_state, done):
        state_tensor = self.preprocess_state(state)
        next_state_tensor = self.preprocess_state(next_state)
        action_idx = self.action_list.index(action)
        self.memory.append((state_tensor, action_idx, reward, next_state_tensor, done))

    def train(self, last_state, last_action, reward, state, done, info=None):
        # Récompense de progression : bonus si Mario avance vers la droite
        progression_bonus = 0
        booster_bonus = 0
        if isinstance(last_state, dict) and isinstance(state, dict):
            x_before = last_state.get("mario_pos", [0, 0])[0]
            x_after = state.get("mario_pos", [0, 0])[0]
            if x_after > x_before:
                progression_bonus = (x_after - x_before) * 0.1  # Bonus proportionnel à l'avancée
            elif x_after < x_before:
                progression_bonus = -0.2  # Petite pénalité si Mario recule
            # Récompense pour le booster (champignon)
            size_before = last_state.get("mario_size", 0)
            size_after = state.get("mario_size", 0)
            if size_after > size_before:
                booster_bonus = 0.5  # Bonus réduit pour le power-up
        reward = reward + progression_bonus + booster_bonus
        self.remember(last_state, last_action, reward, state, done)
        if len(self.memory) < self.batch_size:
            return
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        states = torch.stack(states)
        actions = torch.tensor(actions, device=self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        next_states = torch.stack(next_states)
        dones = torch.tensor(dones, dtype=torch.float32, device=self.device)
        # Q(s,a)
        q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        # Q cible
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target = rewards + self.gamma * next_q * (1 - dones)
        loss = nn.functional.mse_loss(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        # Mise à jour du réseau cible
        self.learn_step += 1
        if self.learn_step % self.update_target_steps == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        # Décroissance epsilon
        if self.exploration_rate > self.epsilon_min:
            self.exploration_rate *= self.epsilon_decay

    # ...garder les méthodes utilitaires (is_near_blocked_position, add_blocked_position)...