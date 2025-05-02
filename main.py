import sys
import pygame
import importlib
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario

# Définition d'une version corrigée de MarioEnv directement dans le fichier principal
# pour éviter les problèmes de cache
class FixedMarioEnv:
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

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

        # Mettre à jour le jeu
        self.mario.update()
        
        # S'assurer que la caméra est mise à jour avec la position de Mario
        self.mario.camera.x = self.mario.rect.x - self.window_size[0] // 2
        if self.mario.camera.x < 0:
            self.mario.camera.x = 0
                
        # Effacer l'écran et dessiner tous les éléments
        self.screen.fill((104, 136, 252))  # Couleur de fond du ciel
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
                import numpy as np
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
                        if hasattr(self.level.level[y][x], 'sprite') and self.level.level[y][x].sprite is not None:
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
            import numpy as np
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

# Import pour le mode IA
from ai.agents.GuidedAgent import GuidedAgent
import numpy as np
import random

windowSize = 640, 480


def main_game(agent_type=None):
    """Fonction pour lancer le jeu normal ou avec IA"""
    pygame.mixer.pre_init(44100, -16, 2, 4096)
    pygame.init()
    screen = pygame.display.set_mode(windowSize)
    pygame.display.set_caption("Super Mario Python")
    
    max_frame_rate = 60
    dashboard = Dashboard("./img/font.png", 8, screen)
    sound = Sound()
    level = Level(screen, sound, dashboard)
    
    # Charger un niveau par défaut (nécessaire pour éviter l'erreur NoneType)
    level.loadLevel("Level1-1")
    
    # Créer le menu avec show_agents=True si on est dans un mode agent
    # Cela permet de passer par le menu de sélection de niveau
    show_agents = agent_type is not None
    menu = Menu(screen, dashboard, level, sound, show_agents=False)  # Ne pas montrer les boutons des agents dans le menu du jeu
    
    # Pour savoir si on doit revenir au menu principal
    retour_menu_principal = False
    
    # Permettre au joueur de choisir un niveau, modifier les paramètres, etc.
    while not menu.start:
        menu.update()
        # Si l'utilisateur appuie sur EXIT dans le menu du jeu
        if menu.state == 2 and pygame.key.get_pressed()[pygame.K_RETURN]:
            retour_menu_principal = True
            break
    
    # Si on veut revenir au menu principal
    if retour_menu_principal:
        return 'menu_principal'
    
    # Mode de jeu avec agent IA
    if agent_type:
        print(f"Démarrage du mode IA avec agent: {agent_type}")
        # Lancer le mode IA avec notre classe corrigée
        env = FixedMarioEnv(agent_type=agent_type)
        
        # Créer l'agent adapté au type choisi
        if agent_type == "guided":
            agent = GuidedAgent()
        else:
            # Si c'est un agent exploratoire ou autre, utiliser simplement des actions aléatoires
            agent = None
        
        # Configurer l'environnement avec le niveau choisi dans le menu
        level_name = menu.levelNames[menu.currSelectedLevel-1] if menu.inChoosingLevel else "Level1-1"
        
        # Boucle de redémarrage pour permettre à l'agent de rejouer le même niveau
        rejouer = True
        while rejouer:
            env.level.loadLevel(level_name)
            state = env.reset()
            done = False
            total_reward = 0
            steps = 0
            max_steps = 5000  # Limite de pas pour éviter les boucles infinies
            
            # Afficher un message indiquant que le niveau commence/recommence
            print(f"L'agent joue au niveau {level_name}")
            
            while not done and steps < max_steps:
                # Gérer les événements de fermeture
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        # Permettre à l'utilisateur d'arrêter le jeu avec Échap
                        if event.key == pygame.K_ESCAPE:
                            rejouer = False
                            done = True
                            print("Retour au menu principal...")
                        # Permettre à l'utilisateur de passer au niveau suivant avec N
                        elif event.key == pygame.K_n:
                            done = True
                            if menu.inChoosingLevel:
                                menu.currSelectedLevel = (menu.currSelectedLevel % len(menu.levelNames)) + 1
                                level_name = menu.levelNames[menu.currSelectedLevel-1]
                                print(f"Passage au niveau suivant: {level_name}")
                
                # Choisir l'action
                if agent:
                    action = agent.choose_action(state)
                else:
                    action = np.random.choice(env.actions)
                
                # Exécuter l'action
                next_state, reward, done, info = env.step(action)
                state = next_state
                total_reward += reward
                steps += 1
                
                # Ralentir un peu l'agent pour voir ce qu'il fait
                pygame.time.delay(10)
            
            # Afficher un message de fin de niveau
            if done:
                if env.mario.rect.y > 450 or (hasattr(env.mario, 'restart') and env.mario.restart):
                    print(f"Mario est mort! Score: {total_reward:.2f}, Étapes: {steps}")
                    
                    # Afficher un message à l'écran pour indiquer comment continuer
                    font = pygame.font.Font(None, 36)
                    text1 = font.render("Mario est mort!", True, (255, 255, 255))
                    text2 = font.render("Appuyez sur R pour recommencer, ESC pour quitter", True, (255, 255, 255))
                    env.screen.blit(text1, (200, 200))
                    env.screen.blit(text2, (80, 250))
                    pygame.display.update()
                    
                    # Attendre l'action de l'utilisateur
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_r:
                                    waiting = False  # Recommencer le niveau
                                elif event.key == pygame.K_ESCAPE:
                                    waiting = False
                                    rejouer = False  # Quitter et retourner au menu
                        pygame.time.delay(100)
                else:
                    print(f"Niveau terminé avec succès! Score: {total_reward:.2f}, Étapes: {steps}")
                    
                    # Afficher un message à l'écran
                    font = pygame.font.Font(None, 36)
                    text1 = font.render("Niveau terminé avec succès!", True, (255, 255, 255))
                    text2 = font.render("Appuyez sur N pour le niveau suivant, ESC pour quitter", True, (255, 255, 255))
                    env.screen.blit(text1, (150, 200))
                    env.screen.blit(text2, (50, 250))
                    pygame.display.update()
                    
                    # Attendre l'action de l'utilisateur
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_n:
                                    # Passer au niveau suivant
                                    if menu.inChoosingLevel:
                                        menu.currSelectedLevel = (menu.currSelectedLevel % len(menu.levelNames)) + 1
                                        level_name = menu.levelNames[menu.currSelectedLevel-1]
                                    waiting = False
                                elif event.key == pygame.K_ESCAPE:
                                    waiting = False
                                    rejouer = False  # Quitter et retourner au menu
                        pygame.time.delay(100)
            elif steps >= max_steps:
                print(f"Nombre d'étapes maximum atteint. Score: {total_reward:.2f}")
                # Afficher un message à l'écran
                font = pygame.font.Font(None, 36)
                text = font.render("Temps écoulé! Appuyez sur R pour recommencer, ESC pour quitter", True, (255, 255, 255))
                env.screen.blit(text, (20, 200))
                pygame.display.update()
                
                # Attendre l'action de l'utilisateur
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                waiting = False  # Recommencer le niveau
                            elif event.key == pygame.K_ESCAPE:
                                waiting = False
                                rejouer = False  # Quitter et retourner au menu
                    pygame.time.delay(100)
        
        env.close()
        return 'menu_principal'  # Retourner au menu principal après l'IA
    else:
        # Mode jeu normal
        mario = Mario(0, 0, level, screen, dashboard, sound)
        clock = pygame.time.Clock()

        while not mario.restart:
            pygame.display.set_caption("Super Mario running with {:d} FPS".format(int(clock.get_fps())))
            if mario.pause:
                mario.pauseObj.update()
            else:
                level.drawLevel(mario.camera)
                dashboard.update()
                mario.update()
            pygame.display.update()
            clock.tick(max_frame_rate)
        
        # Si retour_menu est True, on revient au menu principal
        if hasattr(mario, 'retour_menu') and mario.retour_menu:
            return 'menu_principal'
        else:
            return 'restart'


class MarioButton:
    def __init__(self, screen, x, y, width, height, text):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        
        # Couleurs pour les différents états du bouton
        self.normal_color = (255, 100, 100)
        self.hover_color = (255, 160, 0)
        self.current_color = self.normal_color
        
        # Texte du bouton
        self.font = pygame.font.Font(None, 30)
        self.text_surface = self.font.render(text, True, (255, 255, 255))
        self.text_shadow = self.font.render(text, True, (0, 0, 0))
        self.text_rect = self.text_surface.get_rect(center=(x + width//2, y + height//2))
        
        # Animation
        self.animation_offset = 0
        self.animation_direction = 1
        self.hovered = False
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Animation du bouton
        if self.hovered:
            self.animation_offset += 0.5 * self.animation_direction
            if abs(self.animation_offset) > 3:
                self.animation_direction *= -1
            self.current_color = self.hover_color
        else:
            self.animation_offset = 0
            self.animation_direction = 1
            self.current_color = self.normal_color
    
    def draw(self):
        # Dessiner l'ombre du bouton
        shadow_rect = pygame.Rect(self.x + 4, self.y + 4, self.width, self.height)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), shadow_rect, border_radius=10)
        
        # Dessiner le bouton
        animated_rect = pygame.Rect(
            self.x, 
            self.y + self.animation_offset if self.hovered else self.y, 
            self.width, 
            self.height
        )
        pygame.draw.rect(self.screen, self.current_color, animated_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), animated_rect, width=3, border_radius=10)
        
        # Dessiner l'ombre du texte
        text_shadow_rect = self.text_rect.copy()
        text_shadow_rect.x += 2
        text_shadow_rect.y += 2 + (self.animation_offset if self.hovered else 0)
        self.screen.blit(self.text_shadow, text_shadow_rect)
        
        # Dessiner le texte
        text_pos_rect = self.text_rect.copy()
        text_pos_rect.y += self.animation_offset if self.hovered else 0
        self.screen.blit(self.text_surface, text_pos_rect)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


def afficher_menu_principal():
    """Affiche le menu principal avec les 3 options"""
    pygame.mixer.pre_init(44100, -16, 2, 4096)
    pygame.init()
    screen = pygame.display.set_mode(windowSize)
    pygame.display.set_caption("Super Mario Python - Menu Principal")
    
    # Charger les ressources pour l'arrière-plan
    dashboard = Dashboard("./img/font.png", 8, screen)
    sound = Sound()
    level = Level(screen, sound, dashboard)
    level.loadLevel("Level1-1")  # Nécessaire pour avoir accès aux sprites
    
    # Créer les boutons du menu principal
    buttons = [
        MarioButton(screen, 220, 180, 200, 50, "Jeu Simple"),
        MarioButton(screen, 220, 250, 200, 50, "Agent Guidé"),
        MarioButton(screen, 220, 320, 200, 50, "Agent Exploratoire")
    ]
    
    # Chargement des sprites pour l'animation
    spritesheet = level.sprites.spriteCollection
    mario_sprites = [
        spritesheet.get("mario_run1"),
        spritesheet.get("mario_run2"),
        spritesheet.get("mario_run3")
    ]
    goomba_sprite = spritesheet.get("goomba-1")
    
    # Variables pour l'animation
    mario_x = -50
    mario_frame = 0
    mario_y = 12 * 32
    goomba_positions = [(640 + random.randint(0, 300), 12 * 32) for _ in range(3)]
    cloud_positions = [(640 + random.randint(0, 600), random.randint(30, 100)) for _ in range(5)]
    frame_counter = 0
    
    # Musique de fond - utiliser directement music_channel
    sound.music_channel.play(sound.soundtrack, loops=-1)
    
    clock = pygame.time.Clock()
    running = True
    next_action = None
    
    while running:
        # Gérer les événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            
            # Vérifier les clics sur les boutons
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.is_clicked(event):
                        if sound.allowSFX:
                            sound.play_sfx(sound.coin)  # Effet sonore pour le clic
                        
                        if i == 0:  # Jeu Simple
                            running = False
                            next_action = "normal"
                        elif i == 1:  # Agent Guidé
                            running = False
                            next_action = "guided"
                        elif i == 2:  # Agent Exploratoire
                            running = False
                            next_action = "exploratory"
        
        # Dessiner l'arrière-plan
        for y in range(0, 13):
            for x in range(0, 20):
                screen.blit(spritesheet.get("sky").image, (x * 32, y * 32))
        
        # Dessiner les nuages animés
        for i, (cloud_x, cloud_y) in enumerate(cloud_positions):
            cloud_positions[i] = (cloud_x - 0.5, cloud_y)
            if cloud_x < -100:
                cloud_positions[i] = (640 + random.randint(0, 300), random.randint(30, 100))
            
            for xOff in range(0, 3):
                for yOff in range(0, 2):
                    screen.blit(
                        spritesheet.get(f"cloud{yOff+1}_{xOff+1}").image,
                        (cloud_x + xOff * 32, cloud_y + yOff * 32)
                    )
        
        # Dessiner le sol
        for y in range(13, 15):
            for x in range(0, 20):
                screen.blit(spritesheet.get("ground").image, (x * 32, y * 32))
        
        # Dessiner et animer Mario qui court
        frame_counter += 1
        if frame_counter % 5 == 0:
            mario_frame = (mario_frame + 1) % 3
        
        mario_x += 5
        if mario_x > 640:
            mario_x = -50
            
        screen.blit(mario_sprites[mario_frame].image, (mario_x, mario_y))
        
        # Dessiner et animer les goombas
        for i, (goomba_x, goomba_y) in enumerate(goomba_positions):
            goomba_positions[i] = (goomba_x - 2, goomba_y)
            if goomba_x < -50:
                goomba_positions[i] = (640 + random.randint(0, 300), 12 * 32)
            
            screen.blit(goomba_sprite.image, (goomba_x, goomba_y))
        
        # Dessiner les décorations
        for i in range(5):
            x_pos = 100 + i * 100
            screen.blit(spritesheet.get("bush_1").image, (x_pos, 12 * 32))
            screen.blit(spritesheet.get("bush_2").image, (x_pos + 32, 12 * 32))
            screen.blit(spritesheet.get("bush_3").image, (x_pos + 64, 12 * 32))
        
        # Dessiner le titre
        title_font = pygame.font.Font(None, 64)
        title_text = title_font.render("SUPER MARIO PYTHON", True, (255, 255, 255))
        title_shadow = title_font.render("SUPER MARIO PYTHON", True, (0, 0, 0))
        
        screen.blit(title_shadow, (322, 82))
        screen.blit(title_text, (320, 80))
        
        # Mettre à jour et dessiner les boutons
        for button in buttons:
            button.update()
            button.draw()
        
        pygame.display.flip()
        clock.tick(60)
    
    return next_action


if __name__ == "__main__":
    # Boucle principale entre le menu principal et le jeu
    while True:
        # Afficher le menu principal
        action = afficher_menu_principal()
        
        # Lancer le jeu selon le mode choisi
        if action == "normal":
            result = main_game()
        elif action == "guided":
            result = main_game("guided")
        elif action == "exploratory":
            result = main_game("exploratory")
        
        # Si on ne revient pas au menu principal, sortir de la boucle
        if result != 'menu_principal':
            break
