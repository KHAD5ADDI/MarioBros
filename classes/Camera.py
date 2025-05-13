from classes.Maths import Vec2D


class Camera:
    def __init__(self, pos, entity):
        self.pos = Vec2D(pos.x, pos.y)
        self.entity = entity
        self.x = self.pos.x * 32
        self.y = self.pos.y * 32
        self.smoothness = 0.2  # Augmenté légèrement pour une réaction plus rapide
        self.last_vel_x = 0  # Pour suivre la vitesse de Mario

    def move(self):
        # Obtenir la position de Mario
        xPosFloat = self.entity.getPosIndexAsFloat().x
        
        # Ajuster le décalage en fonction de la vitesse (si disponible)
        offset = 10  # Décalage de base
        if hasattr(self.entity, 'vel'):
            # Mémoriser la vitesse pour avoir une transition plus douce
            self.last_vel_x = self.entity.vel.x * 0.7 + self.last_vel_x * 0.3
            
            # Si Mario va vite vers la droite, ajuster le décalage pour voir plus loin
            if self.last_vel_x > 3:
                # Ajout d'un petit décalage supplémentaire, proportionnel à la vitesse
                # Mais limité pour éviter des mouvements excessifs
                offset += min(3, (self.last_vel_x - 3) * 0.5)

        # Calculer la position cible de la caméra
        target_x = -xPosFloat + offset

        # Interpolation linéaire entre la position actuelle et la position cible
        # Utiliser une valeur de lissage dynamique basée sur la vitesse
        dynamic_smoothness = self.smoothness
        if hasattr(self.entity, 'vel') and abs(self.entity.vel.x) > 3:
            # Augmenter la réactivité quand Mario va vite
            dynamic_smoothness = min(0.5, self.smoothness * (1 + abs(self.entity.vel.x) * 0.05))
            
        self.pos.x = self.pos.x + (target_x - self.pos.x) * dynamic_smoothness

        # Assurer que la caméra ne dépasse pas certaines limites
        if xPosFloat < 10:
            self.pos.x = 0

        # Conversion finale en pixels
        self.x = self.pos.x * 32
        self.y = self.pos.y * 32
