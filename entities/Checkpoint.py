import pygame
import math
from entities.EntityBase import EntityBase

class Checkpoint(EntityBase):
    """
    Classe représentant un checkpoint dans le jeu.
    Le checkpoint est une entité avec laquelle Mario peut interagir.
    """
    
    def __init__(self, x, y, level, sound):
        super(Checkpoint, self).__init__(x, y, 0)  # gravity = 0
        self.level = level
        self.sound = sound
        self.type = "Checkpoint"  # Type d'entité pour les collisions
        self.triggered = False
        self.original_y = y  # Sauvegarder la position Y d'origine pour l'animation de pulsation
          # Charger l'image du checkpoint
        try:
            self.image = pygame.image.load("img/checkpoint.png").convert_alpha()
            # Redimensionner l'image pour la rendre plus visible (128x128 au lieu de 64x64)
            self.image = pygame.transform.scale(self.image, (96, 96))
            # Créer un rectangle légèrement plus grand que l'image pour une meilleure collision
            self.rect = pygame.Rect(x, y - 32, 96, 96)  # Décaler vers le haut pour être visible au-dessus du sol
        except Exception as e:
            print(f"Erreur lors du chargement de l'image checkpoint.png: {e}")
            # Image par défaut en cas d'erreur
            self.image = pygame.Surface((96, 96))
            self.image.fill((255, 0, 0))  # Rouge par défaut
            self.rect = pygame.Rect(x, y - 32, 96, 96)
    
    def update(self, camera=None):
        """
        Mise à jour du checkpoint.
        Cette méthode est appelée à chaque frame.
        """
        # Animation simple du checkpoint (pulsation)
        current_time = pygame.time.get_ticks()
        # Faire pulser légèrement le checkpoint pour attirer l'attention
        pulse = abs(math.sin(current_time / 500)) * 10  # Pulsation entre 0 et 10 pixels
        self.rect.y = self.original_y - int(pulse)
        
    def render(self, camera):
        """
        Affiche le checkpoint à l'écran.
        """
        if hasattr(self.level, 'screen'):
            # Dessiner le checkpoint avec une légère oscillation pour le rendre plus visible
            self.level.screen.blit(self.image, (self.rect.x - camera.x, self.rect.y))
            
            # Dessiner un petit texte d'indication au-dessus du checkpoint
            if hasattr(pygame, 'font') and pygame.font.get_init():
                font = pygame.font.Font(None, 20)
                text = font.render("CHECKPOINT", True, (255, 255, 0))
                text_rect = text.get_rect(centerx=self.rect.x - camera.x + self.rect.width // 2, 
                                          bottom=self.rect.y - 5)
                self.level.screen.blit(text, text_rect)
    
    def checkEntityCollision(self, entity):
        """
        Vérifie si une entité est en collision avec le checkpoint.
        """
        # Simple vérification de collision entre rectangles
        return self.rect.colliderect(entity.rect)