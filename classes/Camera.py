from classes.Maths import Vec2D


class Camera:
    def __init__(self, pos, entity):
        self.pos = Vec2D(pos.x, pos.y)
        self.entity = entity
        self.x = self.pos.x * 32
        self.y = self.pos.y * 32
        self.smoothness = 0.1  # Facteur de lissage pour un mouvement plus fluide

    def move(self):
        xPosFloat = self.entity.getPosIndexAsFloat().x

        # Mouvement de caméra plus doux et plus réactif
        target_x = -xPosFloat + 10

        # Interpolation linéaire entre la position actuelle et la position cible
        self.pos.x = self.pos.x + (target_x - self.pos.x) * self.smoothness

        # Assurer que la caméra ne dépasse pas certaines limites
        if xPosFloat < 10:
            self.pos.x = 0

        self.x = self.pos.x * 32
        self.y = self.pos.y * 32
