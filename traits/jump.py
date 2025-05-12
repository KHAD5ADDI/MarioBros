class JumpTrait:
    def __init__(self, entity):
        self.verticalSpeed = -12  # Restauré à la valeur originale
        self.jumpHeight = 120     # Restauré à la valeur originale
        self.entity = entity
        self.initalHeight = 384
        self.deaccelerationHeight = self.jumpHeight - ((self.verticalSpeed*self.verticalSpeed)/(2*self.entity.gravity))
        self.jumpCooldown = 0    # Conservation du cooldown pour limiter la fréquence des sauts
        self.jumpCooldownTime = 45  # Augmenté pour limiter encore plus la fréquence des sauts

    def jump(self, jumping):
        # Vérifier le cooldown du saut - seule modification conservée de la version précédente
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
                self.entity.obeyGravity = False  # always reach maximum height
                self.jumpCooldown = self.jumpCooldownTime  # Activer le cooldown après un saut

        if self.entity.inJump:
            if (self.initalHeight-self.entity.rect.y) >= self.deaccelerationHeight or self.entity.vel.y == 0:
                self.entity.inJump = False
                self.entity.obeyGravity = True

    def reset(self):
        self.entity.inAir = False
