import pygame

class Projectile:
    def __init__(self, pos, vel, dmg, owner):
        self.pos = pos[:]
        self.vel = vel
        self.damage = dmg
        self.owner = owner
        self.radius = 4

    def update(self, dt, world):
        # move
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

        # colide com parede
        if world.point_in_obstacle(self.pos):
            return False

        # acerta inimigos
        if self.owner.__class__.__name__ == "Player":
            for n in world.npcs:
                if n.alive and (n.pos[0]-self.pos[0])**2 + (n.pos[1]-self.pos[1])**2 < 400:
                    n.health -= self.damage
                    return False
        else:
            p = world.player
            if (p.pos[0]-self.pos[0])**2 + (p.pos[1]-self.pos[1])**2 < 400:
                p.damage(self.damage)
                return False

        return True
