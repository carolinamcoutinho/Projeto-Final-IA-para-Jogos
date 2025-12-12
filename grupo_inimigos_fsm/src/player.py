# player.py
import pygame, math
from utils import normalize, distance
from projectile import Projectile
from config import PLAYER_SPEED, PLAYER_DASH_SPEED, PLAYER_RADIUS, EMP_RADIUS, EMP_DAMAGE, EMP_KNOCKBACK

class Player:
    def __init__(self, world):
        self.world = world
        # start near center
        self.pos = [world.map_w/2, world.map_h/2]
        self.hp = 100
        self.radius = PLAYER_RADIUS
        self.dash_cd = 0.0
        self.emp_cd = 0.0
        self.shoot_cd = 0.0

    def handle_collision(self, newpos):
        # simple collision with obstacles: push back if inside rect
        for r in self.world.obstacles:
            if r.collidepoint(newpos[0], newpos[1]):
                return False
        return True

    def update(self, dt, keys, mouse, camx, camy):
        # movement WASD
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        dirv = [dx, dy]
        # normalize
        from utils import normalize
        if dirv != [0,0]:
            n = normalize(dirv)
            newpos = [self.pos[0] + n[0]*PLAYER_SPEED*dt, self.pos[1] + n[1]*PLAYER_SPEED*dt]
            if self.handle_collision(newpos):
                self.pos = newpos

        # dash (E) towards mouse world pos
        if (keys[pygame.K_e] or keys[pygame.K_KP0]) and self.dash_cd <= 0:
            mx,my = mouse
            # convert mouse screen coords to world coords using cam
            world_mouse = [mx + camx - (self.world.view_w/2), my + camy - (self.world.view_h/2)]
            dirm = [world_mouse[0]-self.pos[0], world_mouse[1]-self.pos[1]]
            if dirm != [0,0]:
                from utils import normalize
                n = normalize(dirm)
                newpos = [self.pos[0] + n[0]*PLAYER_DASH_SPEED*0.18, self.pos[1] + n[1]*PLAYER_DASH_SPEED*0.18]
                if self.handle_collision(newpos):
                    self.pos = newpos
            self.dash_cd = 1.2

        # EMP (Q)
        if (keys[pygame.K_q] or keys[pygame.K_BACKSPACE]) and self.emp_cd <= 0:
            # affect enemies in radius
            for n in self.world.npcs:
                if n.alive:
                    d = distance(self.pos, n.pos)
                    if d <= EMP_RADIUS:
                        n.health -= EMP_DAMAGE
                        # knockback
                        if d>0:
                            nx = (n.pos[0]-self.pos[0])/d
                            ny = (n.pos[1]-self.pos[1])/d
                            n.vel[0] += nx * EMP_KNOCKBACK
                            n.vel[1] += ny * EMP_KNOCKBACK
                        # EMP causes short retreat
                        n.fsm.change(self.world.retreat_state())
            self.emp_cd = 5.0

        # shooting (left mouse)
        if pygame.mouse.get_pressed()[0] and self.shoot_cd <= 0:
            mx,my = mouse
            world_mouse = [mx + camx - (self.world.view_w/2), my + camy - (self.world.view_h/2)]
            dirv = [world_mouse[0]-self.pos[0], world_mouse[1]-self.pos[1]]
            if dirv != [0,0]:
                from utils import normalize, mul
                n = normalize(dirv)
                vel = mul(n, 520.0)
                self.world.spawn_projectile(self.pos[:], vel, dmg=28, owner=None)
                self.shoot_cd = 0.28

        self.dash_cd = max(0.0, self.dash_cd - dt)
        self.emp_cd = max(0.0, self.emp_cd - dt)
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
