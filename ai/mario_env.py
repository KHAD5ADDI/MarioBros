# mario_env.py

import pygame
import numpy as np
import time
import os
import cv2
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
        
        # Position du checkpoint (à ajuster selon votre niveau)
        self.checkpoint_position = 3200  # Position X approximative du checkpoint
        
        # Compteurs pour les statistiques
        self.games_played = 0
        self.max_distance = 0
        self.total_reward_history = []
        
        # Charger l'image de checkpoint pour l'affichage à la victoire
        self.checkpoint_img_surface = None
        for ext in ["png", "jpg"]:
            img_path = os.path.join("img", f"checkpoint.{ext}")
            if os.path.exists(img_path):
                self.checkpoint_img_surface = pygame.image.load(img_path)
                break
        
        # Initialiser l'environnement
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
            key_event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_SPACE})
        elif action == 'select':
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
            levelName = "Level1-1"  # Revenir au niveau 1-1 par défaut
            print(f"Chargement du niveau: {levelName}")
            self.level.loadLevel(levelName)
            # Décaler Mario de 3 pixels vers la droite
            self.mario = Mario(3, 0, self.level, self.screen, self.dashboard, self.sound)
            # Forcer la position de départ de Mario au début du niveau
            self.mario.rect.x = 80 + 3  # Position X initiale (au début du niveau + 3px)
            self.mario.rect.y = 350  # Position Y initiale (sur le sol)
            self.last_x_pos = self.mario.rect.x
            
            # Réinitialiser le compteur de blocage
            self.steps_since_progress = 0
            
            print(f"Mario initialisé à la position: {self.mario.rect.x}, {self.mario.rect.y}")
            return True
        
        return False

    def detect_checkpoint(self):
        """
        Détecte si Mario a atteint le checkpoint en utilisant la reconnaissance d'image.
        Retourne True si le checkpoint est détecté, False sinon.
        """
        if self.checkpoint_image is None:
            return False
            
        try:
            # Capturer l'écran actuel
            screen_array = pygame.surfarray.array3d(self.screen)
            
            # Vérifier que l'écran n'est pas vide
            if screen_array.shape[0] == 0 or screen_array.shape[1] == 0:
                print("Écran de jeu vide, impossible de détecter le checkpoint")
                return False
                
            # S'assurer que l'image modèle est plus petite que l'écran
            screen_height, screen_width = screen_array.shape[0], screen_array.shape[1]
            template = self.checkpoint_image
            
            # Si le template est plus grand que l'écran, le redimensionner
            if template.shape[0] > screen_height or template.shape[1] > screen_width:
                print(f"Redimensionnement du template: {template.shape} -> max({screen_width}, {screen_height})")
                scale = min(screen_width / template.shape[1], screen_height / template.shape[0]) * 0.8
                new_width = int(template.shape[1] * scale)
                new_height = int(template.shape[0] * scale)
                template = cv2.resize(template, (new_width, new_height))
                print(f"Nouvelles dimensions du template: {template.shape}")
            
            # Convertir les images au format compatible avec OpenCV (transposer pour corriger l'orientation)
            screen_array = np.transpose(screen_array, (1, 0, 2))
            
            # Vérifier à nouveau les dimensions
            print(f"Dimensions de l'écran: {screen_array.shape}")
            print(f"Dimensions du template: {template.shape}")
            
            if template.shape[0] > screen_array.shape[0] or template.shape[1] > screen_array.shape[1]:
                print("Le template est toujours plus grand que l'écran après redimensionnement")
                scale = min(screen_array.shape[1] / template.shape[1], screen_array.shape[0] / template.shape[0]) * 0.5
                new_width = int(template.shape[1] * scale)
                new_height = int(template.shape[0] * scale)
                template = cv2.resize(template, (new_width, new_height))
                print(f"Redimensionnement forcé du template: {template.shape}")
            
            # Appliquer la méthode de correspondance de modèle
            result = cv2.matchTemplate(screen_array, template, cv2.TM_CCOEFF_NORMED)
            
            # Trouver la position du meilleur match
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            print(f"Score de correspondance: {max_val:.4f}")
            
            # Si la correspondance est suffisamment bonne, considérer le checkpoint comme détecté
            threshold = 0.6  # Seuil plus bas pour être plus permissif
            
            if max_val >= threshold:
                print(f"CHECKPOINT DÉTECTÉ! Score de correspondance: {max_val:.4f}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Erreur lors de la détection du checkpoint: {e}")
            import traceback
            traceback.print_exc()
            return False

    def handle_gameplay(self, action):
        """Gère les actions pendant le gameplay"""
        reward = 0
        
        print(f"===== DÉBUT HANDLE_GAMEPLAY =====")
        print(f"Action: {action}")
        
        # Réinitialiser TOUTES les actions à chaque frame
        self.mario.traits["goTrait"].direction = 0
        self.mario.traits["jumpTrait"].start = False  # Important: reset jump state
        
        # Simuler les touches de clavier pour contrôler Mario
        if action == 'left':
            self.mario.traits["goTrait"].direction = -1
            print("Mario se déplace vers la gauche")
        elif action == 'right':
            self.mario.traits["goTrait"].direction = 1
            print("Mario se déplace vers la droite")
        elif action == 'jump':
            # Important: définir start à True UNIQUEMENT pour l'action de saut
            self.mario.traits["jumpTrait"].start = True
            # Appeler explicitement la méthode jump() pour que Mario saute réellement
            if hasattr(self.mario.traits["jumpTrait"], "jump"):
                self.mario.traits["jumpTrait"].jump(True)  # Passer True pour indiquer que le saut est activé
            print("Mario saute")
        elif action == 'idle':
            # Ne rien faire, toutes les actions sont déjà réinitialisées
            print("Mario est immobile")
        
        # Force exécution des traits pour appliquer immédiatement les actions
        self.mario.updateTraits()
        
        # Réinitialiser explicitement l'état de saut après la mise à jour
        # pour éviter que le saut ne se répète automatiquement
        if action != 'jump':
            self.mario.traits["jumpTrait"].start = False
        
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
            stats_text = f"IA Mario - Agent {self.agent_type} - Position: {int(self.mario.rect.x)},{int(self.mario.rect.y)}"
            self.screen.blit(font.render(stats_text, True, (255, 255, 255)), (10, 10))
            
            # Afficher les statistiques de jeu
            score_text = f"Parties jouées: {self.games_played} | Score: {self.dashboard.points} | Max distance: {self.max_distance}"
            self.screen.blit(font.render(score_text, True, (255, 255, 255)), (10, 30))
            fps_text = f"FPS: {int(self.clock.get_fps())} | Immobile: {self.steps_since_progress}/240 frames"
            self.screen.blit(font.render(fps_text, True, (255, 255, 255)), (10, 50))
            
            # Dessiner Mario explicitement - CORRECTION POUR L'ORIENTATION
            print("Dessin de Mario via goTrait...")
            animation = self.mario.traits["goTrait"].animation
            # Correction pour l'orientation de Mario (il ne doit pas être à l'envers)
            # Utiliser le heading de Mario plutôt que sa direction de mouvement
            mario_draw_x = self.mario.rect.x - self.mario.camera.x
            mario_draw_y = self.mario.rect.y
            if self.mario.traits["goTrait"].heading == 1:  # Facing right
                self.screen.blit(animation.image, (mario_draw_x, mario_draw_y))
            else:  # Facing left
                self.screen.blit(
                    pygame.transform.flip(animation.image, True, False),
                    (mario_draw_x, mario_draw_y)
                )
            # Affichage de la hitbox de Mario pour le debug
            pygame.draw.rect(self.screen, (255,0,0), pygame.Rect(mario_draw_x, mario_draw_y, self.mario.rect.width, self.mario.rect.height), 2)

            # --- Ajout : Suivi de la position Y de la hitbox de Mario avec le sprite de Mario ---
            # Récupérer la position Y de la hitbox de Mario (au centre de la hitbox)
            mario_hitbox_center_y = self.mario.rect.y + self.mario.rect.height // 2
            # Afficher le sprite de Mario au centre de l'écran, aligné sur la position Y de la hitbox de Mario
            screen_center_x = self.screen.get_width() // 2
            # Décaler de 15 pixels vers la droite (10 précédemment + 5 supplémentaires)
            sprite_image = animation.image
            sprite_rect = sprite_image.get_rect()
            sprite_draw_x = screen_center_x - sprite_rect.width // 2 + 15
            sprite_draw_y = mario_hitbox_center_y - sprite_rect.height // 2
            if self.mario.traits["goTrait"].heading == 1:
                self.screen.blit(sprite_image, (sprite_draw_x, sprite_draw_y))
            else:
                self.screen.blit(pygame.transform.flip(sprite_image, True, False), (sprite_draw_x, sprite_draw_y))
            # --- Fin ajout ---
        
        except Exception as e:
            print(f"ERREUR lors du dessin du niveau: {e}")
            import traceback
            traceback.print_exc()
    
        # Initialiser l'indicateur de mort par blocage
        blocked_death = False
        # Calculer la récompense
        # Récompense pour avancer
        if self.mario.rect.x > self.last_x_pos + 1:
            progress = self.mario.rect.x - self.last_x_pos
            reward += progress * 0.1
            self.steps_since_progress = 0
            # Mettre à jour la distance maximale
            if self.mario.rect.x > self.max_distance:
                self.max_distance = self.mario.rect.x
        else:
            self.steps_since_progress += 1
        # Punir Mario s'il reste immobile trop longtemps (4 secondes = 240 frames à 60 FPS)
        if self.steps_since_progress > 240:  # 4 secondes à 60 FPS
            print("Mario est resté immobile trop longtemps - MORT AUTOMATIQUE!")
            reward -= 100
            self.game_state = "game_over"
            self.done = True
            self.games_played += 1
            blocked_death = True
            # Afficher un message d'erreur sur l'écran
            font = pygame.font.Font(None, 48)
            death_text = font.render("MARIO EST TROP LENT!", True, (255, 0, 0))
            text_rect = death_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(death_text, text_rect)
            pygame.display.update()
            time.sleep(1)  # Afficher le message pendant 1 seconde
        # Pénalité moins sévère si Mario commence à être immobile
        elif self.steps_since_progress > 60:
            reward -= 1
        
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
            self.games_played += 1
        
        # Vérifier si Mario est tombé dans un trou
        if self.mario.rect.y > 450:
            reward -= 100
            self.game_state = "game_over"
            self.done = True
            self.games_played += 1
        
        # Vérifier si Mario a atteint le checkpoint
        if self.mario.rect.x >= self.checkpoint_position:
            print("VICTOIRE! Mario a atteint le checkpoint!")
            reward += 1000  # Grosse récompense pour avoir atteint le checkpoint
            self.game_state = "checkpoint_reached"
            self.done = True
            self.games_played += 1
            # Afficher l'image de checkpoint si elle existe
            if self.checkpoint_img_surface:
                img_rect = self.checkpoint_img_surface.get_rect()
                img_rect.midbottom = (self.screen.get_width() // 2, 13 * 32)
                self.screen.blit(self.checkpoint_img_surface, img_rect)
            # Afficher un message de victoire
            font = pygame.font.Font(None, 48)
            victory_text = font.render("CHECKPOINT ATTEINT!", True, (255, 255, 0))
            text_rect = victory_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 + 60))
            self.screen.blit(victory_text, text_rect)
            pygame.display.update()
            time.sleep(2)  # Afficher le message pendant 2 secondes
        
        print(f"===== FIN HANDLE_GAMEPLAY =====")
        return reward

    def step(self, action):
        """Exécute une action dans l'environnement"""
        reward = 0
        blocked_death = False  # Toujours défini, évite le NameError
        
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
        
        elif self.game_state in ["game_over", "checkpoint_reached"]:
            # Attendre un moment avant de réinitialiser
            time.sleep(1)
            self.done = True
            
            # Ajouter la récompense totale à l'historique
            self.total_reward_history.append(self.total_reward)
            if len(self.total_reward_history) > 10:
                self.total_reward_history.pop(0)
                
            # Afficher des statistiques
            if len(self.total_reward_history) > 0:
                avg_reward = sum(self.total_reward_history) / len(self.total_reward_history)
                print(f"Parties jouées: {self.games_played}, Récompense moyenne: {avg_reward:.2f}")
                print(f"Distance maximale atteinte: {self.max_distance}")
        
        # --- GESTION DU SAUT INUTILE (mortelle) ---
        if action == 'kill_jump':
            print("L'agent a sauté sans raison valable : MORT INSTANTANÉE !")
            self.game_state = "game_over"
            self.done = True
            self.dashboard.points -= 500  # Pénalité très forte
            self.mario.restart = True
            return self.get_state(), -500, True, {"game_state": "game_over", "kill_jump": True}
        
        # Mettre à jour l'écran
        pygame.display.update()
        self.clock.tick(self.max_frame_rate)
        
        self.total_reward += reward
        info = {"game_state": self.game_state}
        if blocked_death:
            info["blocked_death"] = True
        return self.get_state(), reward, self.done, info

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
            # Pour l'agent guidé ou exploratoire dans le gameplay
            if self.agent_type in ["guided", "exploratory"]:
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
    
    def render(self):
        """Cette méthode est implicitement appelée dans step()"""
        pass

    def close(self):
        """Ferme l'environnement"""
        pygame.quit()