import sys
import pygame
from classes.Dashboard import Dashboard
from classes.Level import Level
from classes.Menu import Menu
from classes.Sound import Sound
from entities.Mario import Mario

# Import pour le mode IA - Correction du chemin d'importation
from ai.mario_env import MarioEnv
import numpy as np

windowSize = 640, 480


def main_game():
    """Fonction pour lancer le jeu normal"""
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


def main_ai(agent_type="exploratory"):
    """Fonction pour lancer le mode IA"""
    env = MarioEnv(agent_type=agent_type)
    state = env.reset()
    done = False
    
    while not done:
        # Choisir une action (à remplacer par votre logique d'IA)
        action = np.random.choice(env.actions)
        next_state, reward, done, info = env.step(action)
        state = next_state
    
    env.close()


def run_normal_game():
    exitmessage = 'restart'
    while exitmessage == 'restart':
        exitmessage = main_game()


if __name__ == "__main__":
    # Dans la partie où vous lancez le jeu normal directement
    if len(sys.argv) > 1:
        if sys.argv[1] == "--ai":
            # Si un type d'agent est spécifié
            agent_type = sys.argv[2] if len(sys.argv) > 2 else "exploratory"
            main_ai(agent_type)
        else:
            print("Arguments non reconnus. Démarrage du jeu normal.")
            run_normal_game()
    else:
        # Créer un menu de sélection
        pygame.init()
        screen = pygame.display.set_mode(windowSize)
        pygame.display.set_caption("Super Mario Python - Choisir Mode")
        
        font = pygame.font.Font(None, 36)
        
        buttons = {
            "Jeu Normal": run_normal_game,
            "Agent Guidé": lambda: main_ai("guided"),
            "Agent Exploratoire": lambda: main_ai("exploratory")
        }
        
        button_rects = {}
        y_pos = 150
        
        running = True
        while running:
            screen.fill((0, 0, 0))
            
            title = font.render("Super Mario Python", True, (255, 255, 255))
            screen.blit(title, (320 - title.get_width() // 2, 50))
            
            # Dessiner les boutons
            for i, (name, func) in enumerate(buttons.items()):
                button_color = (100, 100, 255)
                text = font.render(name, True, (255, 255, 255))
                button_rect = pygame.Rect(220, y_pos + i*70, 200, 50)
                button_rects[name] = button_rect
                
                pygame.draw.rect(screen, button_color, button_rect)
                screen.blit(text, (button_rect.centerx - text.get_width() // 2, 
                                 button_rect.centery - text.get_height() // 2))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for name, rect in button_rects.items():
                        if rect.collidepoint(pos):
                            running = False
                            buttons[name]()  # Appeler la fonction associée
            
            pygame.display.flip()
