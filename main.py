import sys
import pygame
import random
import os
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario
from utils import suppress_pygame_warnings

# Import pour le mode IA
from ai.run_agents import run_ai_mario

def main_game():
    """Fonction pour lancer le jeu normal"""
    # Supprimer les avertissements de libpng
    stderr_redirect = suppress_pygame_warnings()
    
    with stderr_redirect():
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("Super Mario Python")
    
    max_frame_rate = 60
    dashboard = Dashboard("./img/font.png", 8, screen)
    sound = Sound()
    level = Level(screen, sound, dashboard)
    
    # Charger un niveau par défaut (nécessaire pour éviter l'erreur NoneType)
    level.loadLevel("Level1-1")
    
    menu = Menu(screen, dashboard, level, sound)
    
    while not menu.start:
        menu.update()
    
    # Si le menu a sélectionné un niveau spécifique, on le charge
    if hasattr(menu, 'selected_level') and menu.selected_level:
        level.loadLevel(menu.selected_level)
    
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
    # Supprimer les avertissements de libpng
    stderr_redirect = suppress_pygame_warnings()
    
    with stderr_redirect():
        pygame.mixer.pre_init(44100, -16, 2, 4096)
        pygame.init()
        screen = pygame.display.set_mode((640, 480))
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
            result = run_ai_mario("guided")
        elif action == "exploratory":
            result = run_ai_mario("exploratory")
        
        # Si on ne revient pas au menu principal, sortir de la boucle
        if result != 'menu_principal':
            break
