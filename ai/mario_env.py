# mario_env.py

import pygame
import numpy as np
import time
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario

class MarioEnv:
    def __init__(self, agent_type="guided"):
        pygame.init()
        self.window_size = (640, 480)
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Super Mario Python - AI Mode")
        self.clock = pygame.time.Clock()
        self.max_frame_rate = 60
        self.agent_type = agent_type

        # État du jeu
        self.game_state = "menu"  # Valeurs possibles: "menu", "level_start", "playing", "game_over"
        
        # Initialiser les composants du jeu
        self.dashboard = Dashboard("./img/font.png", 8, self.screen)
        self.sound = Sound()
        self.level = Level(self.screen, self.sound, self.dashboard)  # Créer le niveau avant le menu
        self.menu = Menu(self.screen, self.dashboard, self.level, self.sound)  # Corriger l'ordre des paramètres
        
        # Ajouter un attribut pour vérifier si Mario est mort
        self.dead = False
        
        # Actions possibles
        self.actions = ['left', 'right', 'jump', 'idle']
        
        # Variables pour suivre la progression
        self.last_x_pos = 0
        self.steps_since_progress = 0
        self.reset()

    def reset(self):
        """Réinitialise l'environnement au début d'un épisode"""
        print("Réinitialisation de l'environnement...")
        
        # Remettre à zéro l'état du jeu et retourner au menu
        self.game_state = "menu"
        self.level = Level(self.screen, self.sound, self.dashboard)  # Réinitialiser le niveau
        self.menu = Menu(self.screen, self.dashboard, self.level, self.sound)  # Corriger l'ordre des paramètres
        self.done = False
        self.total_reward = 0
        
        # Initialiser les variables de suivi
        self.last_x_pos = 0
        self.steps_since_progress = 0
        self.dashboard.coins_collected_last_step = 0
        
        return self.get_state()

    def handle_menu(self, action):
        """Gère les actions dans le menu"""
        # Plutôt que d'essayer d'utiliser un attribut input qui n'existe pas,
        # nous allons simuler directement les touches de clavier
        key_event = None
        
        if action == 'right':
            key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT})
        elif action == 'left':
            key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})
        elif action == 'jump':
            key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN})
        elif action == 'idle':
            return False  # Aucune action
        
        # Injecter l'événement dans la file d'événements pygame
        if key_event:
            pygame.event.post(key_event)
        
        # Mettre à jour le menu
        self.menu.update()
        
        # Vérifier si un niveau a été sélectionné
        if self.menu.start:
            print("Niveau sélectionné, passage à l'état de jeu...")
            self.game_state = "level_start"
            self.level = Level(self.screen, self.sound, self.dashboard)
            levelName = self.menu.levelNames[self.menu.currSelectedLevel-1] if self.menu.inChoosingLevel else "Level1-1"
            self.level.loadLevel(levelName)
            self.mario = Mario(80, 50, self.level, self.screen, self.dashboard, self.sound)
            self.last_x_pos = self.mario.rect.x
            return True
        
        return False

    def handle_gameplay(self, action):
        """Gère les actions pendant le gameplay"""
        reward = 0
        
        print(f"===== DÉBUT HANDLE_GAMEPLAY =====")
        print(f"Action: {action}")
        
        # Simuler les touches de clavier pour contrôler Mario
        if action == 'left':
            self.mario.traits["goTrait"].direction = -1
        elif action == 'right':
            self.mario.traits["goTrait"].direction = 1
        elif action == 'jump':
            self.mario.traits["jumpTrait"].start = True
        elif action == 'idle':
            self.mario.traits["goTrait"].direction = 0
        
        # Réinitialiser le saut si Mario est au sol
        if self.mario.onGround:
            self.mario.traits["jumpTrait"].reset()
        
        print(f"Position de Mario avant mise à jour: {self.mario.rect.x}, {self.mario.rect.y}")
        
        # ÉTAPE 1: Efface l'écran avec une couleur de fond
        print("Effacement de l'écran...")
        self.screen.fill((104, 136, 252))  # Couleur bleu ciel
        
        # ÉTAPE 2: Mise à jour des positions et états
        print("Mise à jour de Mario...")
        self.mario.update()
        print(f"Position de Mario après mise à jour: {self.mario.rect.x}, {self.mario.rect.y}")
        
        # ÉTAPE 3: Dessiner tous les éléments du jeu
        # Forcer le dessin du niveau complet
        try:
            print("Dessin du ciel et du sol...")
            # Dessiner le ciel et le sol d'abord
            for y in range(0, 13):
                for x in range(0, 20):
                    self.screen.blit(
                        self.level.sprites.spriteCollection.get("sky").image,
                        (x * 32, y * 32)  # N'utilise pas la position de la caméra pour le ciel
                    )
            for y in range(13, 15):
                for x in range(0, 20):
                    self.screen.blit(
                        self.level.sprites.spriteCollection.get("ground").image,
                        (x * 32, y * 32)  # N'utilise pas la position de la caméra pour le sol
                    )
            
            # Ensuite dessiner le niveau avec ses objets
            print("Dessin du niveau...")
            self.level.drawLevel(self.mario.camera)
            
            # Puis dessiner le tableau de bord
            print("Mise à jour du tableau de bord...")
            self.dashboard.update()
            
            # Dessiner un texte d'information pour l'agent IA
            font = pygame.font.Font(None, 20)
            text = font.render(f"IA Mario - Agent {self.agent_type} - Position: {int(self.mario.rect.x)},{int(self.mario.rect.y)}", True, (255, 255, 255))
            self.screen.blit(text, (10, 10))
            
            # Dessiner Mario explicitement (la classe Mario n'a pas de méthode draw() directe)
            print("Dessin de Mario via goTrait...")
            # Au lieu d'appeler self.mario.draw(), nous forçons le dessin via le trait d'animation
            # qui est responsable du rendu de Mario dans le jeu original
            animation = self.mario.traits["goTrait"].animation
            if self.mario.traits["goTrait"].direction == 1:
                self.screen.blit(animation.image, (self.mario.rect.x - self.mario.camera.x, self.mario.rect.y))
            else:
                self.screen.blit(
                    pygame.transform.flip(animation.image, True, False),
                    (self.mario.rect.x - self.mario.camera.x, self.mario.rect.y)
                )
        
        except Exception as e:
            print(f"ERREUR lors du dessin du niveau: {e}")
            import traceback
            traceback.print_exc()
    
        # Calculer la récompense
        # Récompense pour avancer
        if self.mario.rect.x > self.last_x_pos + 1:
            reward += (self.mario.rect.x - self.last_x_pos) * 0.1
            self.steps_since_progress = 0
        else:
            self.steps_since_progress += 1
        
        # Pénalité si Mario reste bloqué trop longtemps
        if self.steps_since_progress > 60:
            reward -= 1
            if self.steps_since_progress > 120:
                # Action aléatoire pour débloquer
                self.mario.traits["goTrait"].direction = np.random.choice([-1, 1])
                self.mario.traits["jumpTrait"].start = True
        
        # Mettre à jour la dernière position x
        self.last_x_pos = self.mario.rect.x
        
        # Récompense pour collecter des pièces
        if hasattr(self.dashboard, 'coins_collected_last_step'):
            coins_collected = self.dashboard.coins - self.dashboard.coins_collected_last_step
            if coins_collected > 0:
                reward += coins_collected * 5
        self.dashboard.coins_collected_last_step = self.dashboard.coins
        
        # Vérifier si Mario est mort ou a fini le niveau
        if hasattr(self.mario, 'restart') and self.mario.restart:
            reward -= 100
            self.game_state = "game_over"
            self.done = True
        
        # Vérifier si Mario est tombé dans un trou
        if self.mario.rect.y > 450:
            reward -= 100
            self.game_state = "game_over"
            self.done = True
        
        print(f"===== FIN HANDLE_GAMEPLAY =====")
        return reward

    def step(self, action):
        """Exécute une action dans l'environnement"""
        reward = 0
        
        # Gérer les événements pygame pour éviter que l'application ne se bloque
        pygame.event.pump()
        
        # Gérer les différents états du jeu
        if self.game_state == "menu":
            level_selected = self.handle_menu(action)
            if level_selected:
                reward += 5  # Récompense pour avoir sélectionné un niveau
        
        elif self.game_state == "level_start":
            # Transition rapide pour commencer le niveau
            self.game_state = "playing"
            reward += 2  # Petite récompense pour commencer à jouer
        
        elif self.game_state == "playing":
            reward += self.handle_gameplay(action)
        
        elif self.game_state == "game_over":
            # Attendre un moment avant de réinitialiser
            time.sleep(1)
            self.done = True
        
        # Mettre à jour l'écran
        pygame.display.update()
        self.clock.tick(self.max_frame_rate)
        
        self.total_reward += reward
        return self.get_state(), reward, self.done, {"game_state": self.game_state}

    def get_state(self):
        """Retourne une représentation de l'état actuel du jeu"""
        if self.game_state == "menu":
            # État simplifié pour le menu
            return {
                "game_state": "menu",
                "mario_pos": [0, 0],
                "mario_vel": [0, 0],
                "nearby_objects": [],
                "coins": 0,
                "score": 0
            }
        
        elif self.game_state in ["playing", "level_start"]:
            # Pour l'agent guidé dans le gameplay
            if self.agent_type == "guided":
                mario_x, mario_y = self.mario.rect.x, self.mario.rect.y
                nearby_objects = []
                
                # Collecter les entités
                try:
                    for entity in self.level.entityList:
                        if entity != self.mario and hasattr(entity, 'rect'):
                            rel_x = entity.rect.x - mario_x
                            rel_y = entity.rect.y - mario_y
                            if abs(rel_x) < 200 and abs(rel_y) < 200:
                                entity_type = entity.__class__.__name__
                                nearby_objects.append([rel_x, rel_y, entity_type])
                except Exception as e:
                    print(f"Erreur lors de la collecte des entités: {e}")
                
                # Collecter les tuiles
                try:
                    visible_area_x_start = max(0, int((mario_x - 200) / 32))
                    visible_area_x_end = min(self.level.levelLength, int((mario_x + 200) / 32) + 1)
                    visible_area_y_start = max(0, int((mario_y - 200) / 32))
                    visible_area_y_end = min(15, int((mario_y + 200) / 32) + 1)
                    
                    for y in range(visible_area_y_start, visible_area_y_end):
                        for x in range(visible_area_x_start, visible_area_x_end):
                            if self.level.level[y][x] != 0:
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
                    "game_state": self.game_state,
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
            # Pour l'agent exploratoire
            else:
                return np.array([
                    self.mario.rect.x, 
                    self.mario.rect.y,
                    self.mario.vel.x,
                    self.mario.vel.y,
                    self.mario.powerUpState
                ])
        
        elif self.game_state == "game_over":
            # État pour fin de jeu
            return {
                "game_state": "game_over",
                "mario_pos": [0, 0],
                "mario_vel": [0, 0],
                "nearby_objects": [],
                "coins": self.dashboard.coins,
                "score": self.dashboard.points
            }
    
    def render(self):
        """Cette méthode est implicitement appelée dans step()"""
        pass

    def close(self):
        """Ferme l'environnement"""
        pygame.quit()