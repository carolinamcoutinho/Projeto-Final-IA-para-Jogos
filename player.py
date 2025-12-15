# player.py
import pygame
from utils import normalize, distance, mul

class Player:
    def __init__(self, world):
        self.world = world
        self.pos = [world.map_w/2, world.map_h/2]
        self.vel = [0.0, 0.0]
        self.radius = 16

        # vida
        self.max_hp = 120
        self.hp = self.max_hp
        self.alive = True

        # cooldowns
        self.dash_cd = 0.0
        self.emp_cd = 0.0
        self.shoot_cd = 0.0

        # parâmetros
        self.move_speed = 220
        self.dash_force = 750

    # ---------------------------------------
    # DANO
    # ---------------------------------------
    def damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.world.on_player_death()

    # ---------------------------------------
    # PODERES
    # ---------------------------------------
    def use_dash(self):
        if self.dash_cd > 0:
            return
        
        # mesmo parado, dash funciona agora
        d = normalize(self.vel)
        if d == [0,0]:
            d = [1,0]  # direção padrão
        
        self.vel[0] = d[0] * self.dash_force
        self.vel[1] = d[1] * self.dash_force
        self.dash_cd = 1.0  # mais rápido

        print("DASH!")

    def use_emp(self):
        if self.emp_cd > 0:
            return

        print("EMP!")

        for n in self.world.npcs:
            if n.alive and distance(self.pos, n.pos) < 160:
                n.health -= 20
                # stun leve
                n.vel = [0,0]
                n.stunned = 0.6
                n.fsm.change(self.world.retreat_state())

        self.emp_cd = 4.0

    def shoot(self, mouse_world):
        if self.shoot_cd > 0:
            return

        print("SHOOT!")

        dx = mouse_world[0] - self.pos[0]
        dy = mouse_world[1] - self.pos[1]

        n = normalize([dx, dy])
        vel = mul(n, 520)

        self.world.spawn_projectile(self.pos[:], vel, dmg=28, owner=self)
        self.shoot_cd = 0.25

    # ---------------------------------------
    # UPDATE
    # ---------------------------------------
    def update(self, dt, keys, mouse, camx, camy):
        if not self.alive:
            return

        # mouse world coord
        mouse_world = (
            mouse[0] + camx - self.world.view_w//2,
            mouse[1] + camy - self.world.view_h//2
        )

        # movimento
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])

        if dx != 0 or dy != 0:
            n = normalize([dx, dy])
            self.vel[0] += n[0] * self.move_speed * dt
            self.vel[1] += n[1] * self.move_speed * dt
        else:
            self.vel[0] *= 0.88
            self.vel[1] *= 0.88

        # poderes
        if keys[pygame.K_SPACE]:
            self.use_dash()

        if keys[pygame.K_e]:
            self.use_emp()

        if pygame.mouse.get_pressed()[0]:
            self.shoot(mouse_world)

        # movement clamp
        spd = (self.vel[0]**2 + self.vel[1]**2)**0.5
        max_spd = 280
        if spd > max_spd:
            k = max_spd/spd
            self.vel[0] *= k
            self.vel[1] *= k
        self.world.clamp_to_bounds(self.pos, self.radius)
        
        # aplicar movimento
        newx = self.pos[0] + self.vel[0]*dt
        newy = self.pos[1] + self.vel[1]*dt

        if not self.world.point_in_obstacle((newx, newy)):
            self.pos = [newx, newy]
        else:
            self.vel = [0,0]

        # cooldowns
        self.dash_cd = max(0, self.dash_cd - dt)
        self.emp_cd = max(0, self.emp_cd - dt)
        self.shoot_cd = max(0, self.shoot_cd - dt)
