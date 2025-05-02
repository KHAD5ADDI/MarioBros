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
        
        # Charger un niveau par défaut
        self.level.loadLevel("Level1-1")
        
        # Ajouter un attribut pour vérifier si Mario est mort
        self.dead = False
        
        # Actions possibles
        self.actions = ['left', 'right', 'jump', 'idle']
        
        # Variables pour suivre la progression
        self.last_x_pos = 0
        self.steps_since_progress = 0
        
        self.reset()

    def reset(self):
        # Créer une nouvelle instance de Mario au point de départ
        self.mario = Mario(80, 50, self.level, self.screen, self.dashboard, self.sound)
        self.done = False
        self.total_reward = 0
        self.last_x_pos = self.mario.rect.x
        self.steps_since_progress = 0
        
        # S'assurer que la caméra est correctement initialisée
        self.mario.camera.x = 0
        self.mario.camera.y = 0
        
        # Initialiser le tableau de bord
        if not hasattr(self.dashboard, 'coins_collected_last_step'):
            self.dashboard.coins_collected_last_step = 0
        
        return self.get_state()

    def step(self, action):
        reward = 0
        
        # Gérer les événements pygame pour éviter que l'application ne se bloque
        pygame.event.pump()

        # Simuler les touches de clavier pour contrôler Mario
        if action == 'left':
            self.mario.traits["goTrait"].direction = -1
        elif action == 'right':
            self.mario.traits["goTrait"].direction = 1
        elif action == 'jump':
            self.mario.traits["jumpTrait"].start = True
        elif action == 'idle':
            self.mario.traits["goTrait"].direction = 0

        # Réinitialiser le saut de Mario s'il est au sol
        if self.mario.onGround:  # Utiliser directement l'attribut onGround de Mario
            self.mario.traits["jumpTrait"].reset()

        # Mettre à jour le jeu
        self.mario.update()
        self.level.drawLevel(self.mario.camera)
        self.dashboard.update()
        pygame.display.update()
        self.clock.tick(self.max_frame_rate)

        # Calculer la récompense
        # Récompense pour avancer
        if self.mario.rect.x > self.last_x_pos + 1:  # +1 pour éviter de récompenser des mouvements minimes
            reward += (self.mario.rect.x - self.last_x_pos) * 0.1
            self.steps_since_progress = 0
        else:
            self.steps_since_progress += 1
        
        # Pénalité si Mario reste bloqué trop longtemps
        if self.steps_since_progress > 60:  # environ 1 seconde
            reward -= 1
            # Si bloqué trop longtemps, forcer une action aléatoire
            if self.steps_since_progress > 120:
                self.mario.traits["goTrait"].direction = np.random.choice([-1, 1])
                self.mario.traits["jumpTrait"].start = True
        
        # Mettre à jour la dernière position x
        self.last_x_pos = self.mario.rect.x
        
        # Récompense pour collecter des pièces
        if hasattr(self.dashboard, 'coins_collected_last_step'):
            coins_collected = self.dashboard.coins - self.dashboard.coins_collected_last_step
            if coins_collected > 0:
                reward += coins_collected * 5  # Bonus pour les pièces
        self.dashboard.coins_collected_last_step = self.dashboard.coins

        # Vérifier si Mario est mort
        if hasattr(self.mario, 'restart') and self.mario.restart:
            reward -= 100  # Pénalité pour la mort
            self.done = True
        
        # Vérifier si Mario est tombé dans un trou
        if self.mario.rect.y > 450:  # Position y élevée = tombé dans un trou
            reward -= 100
            self.done = True

        self.total_reward += reward
        return self.get_state(), reward, self.done, {}

    def get_state(self):
        # Retourner une représentation de l'état actuel
        # Pour l'agent guidé
        if self.agent_type == "guided":
            # Récupérer les informations sur les objets proches
            mario_x, mario_y = self.mario.rect.x, self.mario.rect.y
            nearby_objects = []
            
            # Collecter les entités
            try:
                for entity in self.level.entityList:
                    if entity != self.mario and hasattr(entity, 'rect'):
                        # Position relative à Mario
                        rel_x = entity.rect.x - mario_x
                        rel_y = entity.rect.y - mario_y
                        if abs(rel_x) < 200 and abs(rel_y) < 200:  # Objets dans un rayon de 200 pixels
                            entity_type = entity.__class__.__name__
                            nearby_objects.append([rel_x, rel_y, entity_type])
            except Exception as e:
                print(f"Erreur lors de la collecte des entités: {e}")
            
            # Collecter les tuiles (murs, plateformes, etc.)
            try:
                # Approximation des tuiles visibles autour de Mario
                visible_area_x_start = max(0, int((mario_x - 200) / 32))
                visible_area_x_end = min(self.level.levelLength, int((mario_x + 200) / 32) + 1)  # Utilisez levelLength au lieu de length
                visible_area_y_start = max(0, int((mario_y - 200) / 32))
                visible_area_y_end = min(15, int((mario_y + 200) / 32) + 1)
                
                for y in range(visible_area_y_start, visible_area_y_end):
                    for x in range(visible_area_x_start, visible_area_x_end):
                        if self.level.level[y][x] != 0:  # Si ce n'est pas un espace vide
                            tile_x = x * 32
                            tile_y = y * 32
                            rel_x = tile_x - mario_x
                            rel_y = tile_y - mario_y
                            if abs(rel_x) < 200 and abs(rel_y) < 200:
                                nearby_objects.append([rel_x, rel_y, "Tile"])
            except Exception as e:
                print(f"Erreur lors de la collecte des tuiles: {e}")
            
            # Créer et retourner l'état
            state = {
                "mario_pos": [mario_x, mario_y],
                "mario_vel": [self.mario.vel.x, self.mario.vel.y],
                "mario_size": self.mario.powerUpState,
                "nearby_objects": nearby_objects,
                "coins": self.dashboard.coins,
                "score": self.dashboard.points,
                "time": self.dashboard.time,
                "camera_x": self.mario.camera.x,
                "camera_y": self.mario.camera.y
            }
            return state
        # Pour l'agent exploratoire (données brutes)
        else:
            # Représentation plus simple: position, vélocité, taille
            return np.array([
                self.mario.rect.x, 
                self.mario.rect.y,
                self.mario.vel.x,
                self.mario.vel.y,
                self.mario.powerUpState
            ])

    def render(self):
        # Cette méthode est maintenant implicitement appelée dans step()
        pass

    def close(self):
        pygame.quit()