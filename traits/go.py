from pygame.transform import flip


class GoTrait:
    def __init__(self, animation, screen, camera, ent):
        self.animation = animation
        self.direction = 0
        self.heading = 1
        self.accelVel = 0.2  # Réduit de 0.4 à 0.2 pour une accélération plus douce
        self.decelVel = 0.15  # Réduit de 0.25 à 0.15 pour une décélération plus douce
        self.maxVel = 2.5  # Réduit de 3.0 à 2.5 pour une vitesse maximale plus basse
        self.screen = screen
        self.boost = False
        self.camera = camera
        self.entity = ent

    def update(self):
        if self.boost:
            self.maxVel = 4.0  # Vitesse maximale en mode boost
            self.animation.deltaTime = 4
        else:
            self.animation.deltaTime = 7
            self.maxVel = 3.2  # Vitesse normale

        # Vérifier et limiter la vitesse à 3.3 pixels par frame maximum
        # sans tuer Mario, juste ralentir si nécessaire
        MAX_SAFE_SPEED = 3.3  # Vitesse maximale autorisée
        if abs(self.entity.vel.x) > MAX_SAFE_SPEED:
            # Ralentir Mario en respectant sa direction
            self.entity.vel.x = MAX_SAFE_SPEED * (1 if self.entity.vel.x > 0 else -1)
            print(f"Vitesse limitée à {MAX_SAFE_SPEED} pixels/frame")

        if self.direction != 0:
            self.heading = self.direction
            if self.heading == 1:
                if self.entity.vel.x < self.maxVel:
                    self.entity.vel.x += self.accelVel * self.heading
            else:
                if self.entity.vel.x > -self.maxVel:
                    self.entity.vel.x += self.accelVel * self.heading

            # Vérifier à nouveau la limite de vitesse après l'accélération
            if abs(self.entity.vel.x) > MAX_SAFE_SPEED:
                self.entity.vel.x = MAX_SAFE_SPEED * (1 if self.entity.vel.x > 0 else -1)

            if not self.entity.inAir:
                self.animation.update()
            else:
                self.animation.inAir()
        else:
            self.animation.update()
            if self.entity.vel.x >= 0:
                self.entity.vel.x -= self.decelVel
            else:
                self.entity.vel.x += self.decelVel
            if int(self.entity.vel.x) == 0:
                self.entity.vel.x = 0
                if self.entity.inAir:
                    self.animation.inAir()
                else:
                    self.animation.idle()
        if (self.entity.invincibilityFrames//2) % 2 == 0:
            self.drawEntity()

    def updateAnimation(self, animation):
        self.animation = animation
        self.update()

    def drawEntity(self):
        # Obtenir la position actuelle de la hitbox
        pos = self.entity.getPos()
        
        # Calculer la position exacte pour le rendu du sprite
        # en tenant compte des potentielles différences de dimensions
        sprite_width = self.animation.image.get_width()
        sprite_height = self.animation.image.get_height()
        rect_width = self.entity.rect.width
        rect_height = self.entity.rect.height
        
        # Position exacte pour que l'image suive parfaitement la hitbox
        sprite_x = pos[0]
        sprite_y = pos[1] + rect_height - sprite_height
        
        # Afficher le sprite à la position calculée
        # Ne pas faire de traitement différent selon la direction puisque 
        # nous utilisons une image fixe sans animation
        self.screen.blit(self.animation.image, (sprite_x, sprite_y))
