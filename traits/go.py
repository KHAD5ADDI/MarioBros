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
        pos = self.entity.getPos()  # (rect.x, rect.y)
        cam_x = self.camera.x if self.camera else 0
        cam_y = self.camera.y if self.camera else 0

        # Taille de la hitbox et du sprite
        rect_width = self.entity.rect.width
        rect_height = self.entity.rect.height
        sprite_width = self.animation.image.get_width()
        sprite_height = self.animation.image.get_height()

        # Calculer le décalage pour centrer le sprite sur la hitbox
        offset_x = (rect_width - sprite_width) // 2
        offset_y = (rect_height - sprite_height) // 2

        # Position exacte pour que le sprite soit centré sur la hitbox
        sprite_x = pos[0] - cam_x + offset_x
        sprite_y = pos[1] - cam_y + offset_y

        self.screen.blit(self.animation.image, (sprite_x, sprite_y))