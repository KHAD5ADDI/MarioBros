class JumpTrait:
    def __init__(self, entity):
        self.verticalSpeed = -14  # Augmenté pour un saut encore plus haut
        self.jumpHeight = 160   # Augmenté pour une hauteur maximale plus importante
        self.entity = entity
        self.initalHeight = 384
        self.deaccelerationHeight = self.jumpHeight - ((self.verticalSpeed*self.verticalSpeed)/(2*self.entity.gravity))
        self.jumpCooldown = 0    
        self.jumpCooldownTime = 30

    def jump(self, jumping):
        # Vérifier le cooldown du saut
        if self.jumpCooldown > 0:
            self.jumpCooldown -= 1
            return  # Ne pas sauter pendant le cooldown

        if jumping:
            if self.entity.onGround:
                self.entity.sound.play_sfx(self.entity.sound.jump)
                self.entity.vel.y = self.verticalSpeed
                self.entity.inAir = True
                self.initalHeight = self.entity.rect.y
                self.entity.inJump = True
                # Activons toujours la gravité pour un saut plus naturel
                self.entity.obeyGravity = True  
                self.jumpCooldown = self.jumpCooldownTime

        if self.entity.inJump:
            # Permettre à la gravité d'agir plus rapidement sur Mario
            if (self.initalHeight-self.entity.rect.y) >= self.deaccelerationHeight or self.entity.vel.y >= 0:
                self.entity.inJump = False
                self.entity.obeyGravity = True

    def reset(self):
        self.entity.inAir = False
