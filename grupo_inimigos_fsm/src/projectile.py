# projectile.py
from utils import distance

class Projectile:
    def __init__(self, pos, vel, dmg, owner=None):
        self.pos = pos[:]
        self.vel = vel[:]
        self.dmg = dmg
        self.owner = owner
        self.ttl = 2.0
    def update(self, dt, world):
        self.pos[0] += self.vel[0]*dt
        self.pos[1] += self.vel[1]*dt
        self.ttl -= dt
        if self.ttl <= 0:
            return False
        # collision with NPCs
        for n in world.npcs:
            if n.alive and n is not self.owner:
                if distance(self.pos, n.pos) < n.radius:
                    n.health -= self.dmg
                    # if death -> world handles retreat
                    return False
        return True
