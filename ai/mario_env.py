# mario_env.py

import pygame
import numpy as np
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario

class MarioEnv:
    def __init__(self, agent_type="exploratory"):
        pygame.init()
        self.window_size = (640, 480)
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Super Mario Python - AI Mode")
        self.clock = pygame.time.Clock()
        self.max_frame_rate = 60
        self.agent_type = agent_type

        self.dashboard = Dashboard("./img/font.png", 8, self.screen)
        self.sound = Sound()
        self.level = Level(self.screen, self.sound, self.dashboard)
        self.menu = Menu(self.screen, self.dashboard, self.level, self.sound)
        
        # Charger un niveau par défaut
        self.level.loadLevel("Level1-1")
        
        self.actions = ['left', 'right', 'jump', 'idle']
        self.reset()

    def reset(self):
        self.mario = Mario(0, 0, self.level, self.screen, self.dashboard, self.sound)
        self.done = False
        self.total_reward = 0
        return self.get_state()

    def step(self, action):
        reward = 0

        # Simuler les touches de clavier pour contrôler Mario
        keys = pygame.key.get_pressed()
        if action == 'left':
            # Simuler la touche gauche
            self.mario.traits["goTrait"].direction = -1
        elif action == 'right':
            # Simuler la touche droite
            self.mario.traits["goTrait"].direction = 1
        elif action == 'jump':
            # Simuler un saut
            self.mario.traits["jumpTrait"].start = True
        elif action == 'idle':
            # Ne rien faire
            self.mario.traits["goTrait"].direction = 0

        # Mettre à jour le jeu
        self.mario.update()
        self.level.drawLevel(self.mario.camera)
        self.dashboard.update()
        pygame.display.update()
        self.clock.tick(self.max_frame_rate)

        # Calculer la récompense
        reward += self.mario.rect.x * 0.01  # Récompense pour avancer
        if self.mario.dead:
            reward -= 100  # Pénalité pour la mort
            self.done = True

        self.total_reward += reward
        return self.get_state(), reward, self.done, {}

    def get_state(self):
        # Retourner une représentation de l'état actuel
        # Pour l'agent guidé
        if self.agent_type == "guided":
            # Récupérer les informations sur les objets proches
            mario_x, mario_y = self.mario.rect.x, self.mario.rect.y
            enemies = []
            for enemy in self.level.entityList:
                if enemy != self.mario:
                    rel_x = enemy.rect.x - mario_x
                    rel_y = enemy.rect.y - mario_y
                    if abs(rel_x) < 200 and abs(rel_y) < 200:  # Objets dans un rayon de 200 pixels
                        enemies.append([rel_x, rel_y, type(enemy).__name__])
            
            return {
                "mario_pos": [mario_x, mario_y],
                "mario_vel": [self.mario.vel.x, self.mario.vel.y],
                "mario_size": self.mario.big,
                "nearby_objects": enemies,
                "coins": self.dashboard.coins,
                "score": self.dashboard.points,
                "time": self.dashboard.time
            }
        # Pour l'agent exploratoire (données brutes)
        else:
            # Représentation plus simple: position, vélocité, taille
            return np.array([
                self.mario.rect.x, 
                self.mario.rect.y,
                self.mario.vel.x,
                self.mario.vel.y,
                1 if self.mario.big else 0
            ])

    def render(self):
        # Afficher l'état actuel (déjà fait dans step)
        pass

    def close(self):
        pygame.quit()