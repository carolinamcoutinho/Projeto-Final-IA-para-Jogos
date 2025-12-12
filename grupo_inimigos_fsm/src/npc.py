# npc.py
import random
from utils import distance, normalize, sub, add, mul
from steering import seek, separation, cohesion, alignment, flee
from fsm import FSM, Patrol, Engage, Retreat, Dead
from config import NPC_MAX_SPEED, NPC_RADIUS, CHARGE_COOLDOWN, CHARGE_SPEED, PATH_REPLAN_INTERVAL, DETECTION_RANGE
from projectile import Projectile

class BaseNPC:
    def __init__(self, world, x, y):
        self.world = world
        self.pos = [float(x), float(y)]
        self.vel = [0.0, 0.0]
        self.radius = NPC_RADIUS
        self.health = 100.0
        self.max_speed = NPC_MAX_SPEED
        self.alive = True

        self.fsm = FSM(self)
        self.fsm.change(Patrol())

        self.patrol_target = self.pos[:]
        self.charge_cd = 0.0

        # pathfinding
        self.path = None
        self.path_idx = 0
        self.next_replan = 0.0
        self.stunned = 0.0  # for EMP stun

    def pick_patrol_target(self):
        self.patrol_target = [
            random.randint(60, self.world.map_w - 60),
            random.randint(60, self.world.map_h - 60),
        ]

    def neighbors(self):
        return [
            n for n in self.world.npcs
            if n is not self and n.alive and distance(self.pos, n.pos) < 140
        ]

    def can_see_player(self):
        return distance(self.pos, self.world.player.pos) < DETECTION_RANGE

    def behavior_patrol(self, dt):
        if distance(self.pos, self.patrol_target) < 12:
            self.pick_patrol_target()
        desired = seek(self.pos, self.patrol_target, self.max_speed * 0.45)
        self.apply_force(desired, dt)

    def behavior_engage(self, dt):
        if self.stunned > 0:
            self.stunned -= dt
            return

        player_pos = self.world.player.pos
        neigh = self.neighbors()

        s = separation(self, neigh)
        c = cohesion(self, neigh)
        a = alignment(self, neigh)
        sk = seek(self.pos, player_pos, self.max_speed)

        force = [
            sk[0] + s[0] * 1.2 + c[0] * 0.35 + a[0] * 0.4,
            sk[1] + s[1] * 1.2 + c[1] * 0.35 + a[1] * 0.4,
        ]

        # melee damage
        if distance(self.pos, player_pos) < 22:
            self.world.player.damage(18 * dt)

        # pathfinding replan
        self.next_replan -= dt
        if (self.path is None or self.next_replan <= 0):
            self.plan_path_to(player_pos)
            self.next_replan = PATH_REPLAN_INTERVAL

        # follow path waypoints if exist
        if self.path:
            if self.path_idx < len(self.path):
                wp = self.path[self.path_idx]
                wx = wp[0] * self.world.tile + self.world.tile / 2
                wy = wp[1] * self.world.tile + self.world.tile / 2

                if distance(self.pos, (wx, wy)) < 10:
                    self.path_idx += 1
                else:
                    pseek = seek(self.pos, (wx, wy), self.max_speed)
                    force = [
                        pseek[0] + s[0] * 1.2 + a[0] * 0.4,
                        pseek[1] + s[1] * 1.2 + a[1] * 0.4,
                    ]

        # charge ability
        if self.charge_cd <= 0 and distance(self.pos, player_pos) > 70:
            d = normalize([player_pos[0] - self.pos[0], player_pos[1] - self.pos[1]])
            self.vel = mul(d, CHARGE_SPEED)
            self.charge_cd = CHARGE_COOLDOWN
        else:
            self.apply_force(force, dt)

        self.charge_cd = max(0.0, self.charge_cd - dt)

    def behavior_retreat(self, dt):
        f = flee(self.pos, self.world.player.pos, self.max_speed * 0.9)
        self.apply_force(f, dt)

    def apply_force(self, desired_vel, dt):
        # velocity smoothing
        self.vel[0] += (desired_vel[0] - self.vel[0]) * dt * 6.0
        self.vel[1] += (desired_vel[1] - self.vel[1]) * dt * 6.0

        # clamp speed
        speed = (self.vel[0]**2 + self.vel[1]**2) ** 0.5
        if speed > self.max_speed:
            k = self.max_speed / speed
            self.vel[0] *= k
            self.vel[1] *= k

        newx = self.pos[0] + self.vel[0] * dt
        newy = self.pos[1] + self.vel[1] * dt

        if not self.world.point_in_obstacle((newx, newy)):
            self.pos[0] = newx
            self.pos[1] = newy
        else:
            self.vel = [0.0, 0.0]

    def update(self, dt):
        if not self.alive:
            return
        self.fsm.update(dt)
        if self.health <= 0 and self.alive:
            self.alive = False
            for n in self.world.npcs:
                if n.alive:
                    n.fsm.change(self.world.retreat_state())

    def plan_path_to(self, world_pos):
        tx = int(world_pos[0] // self.world.tile)
        ty = int(world_pos[1] // self.world.tile)
        sx = int(self.pos[0] // self.world.tile)
        sy = int(self.pos[1] // self.world.tile)

        path = self.world.astar((sx, sy), (tx, ty))
        if path:
            self.path = path
            self.path_idx = 0
        else:
            self.path = None
            self.path_idx = 0


class Brute(BaseNPC):
    COLOR = (255, 74, 74)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 220
        self.max_speed = 110
        self.charge_cd = 0.0


class Shooter(BaseNPC):
    COLOR = (255, 229, 93)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 100
        self.max_speed = 150
        self.shoot_cd = 0.0

    def behavior_engage(self, dt):
        super().behavior_engage(dt)

        # shooting behavior
        self.shoot_cd -= dt
        player = self.world.player
        if self.shoot_cd <= 0 and distance(self.pos, player.pos) < 420:
            d = normalize([player.pos[0] - self.pos[0], player.pos[1] - self.pos[1]])
            vel = mul(d, 440)
            self.world.spawn_projectile(self.pos[:], vel, dmg=18, owner=self)
            self.shoot_cd = 1.0


class Support(BaseNPC):
    COLOR = (194, 111, 255)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 110
        self.max_speed = 140
        self.heal_cd = 0.0

    def behavior_engage(self, dt):
        self.heal_cd -= dt
        if self.heal_cd <= 0:
            for n in self.world.npcs:
                if n is not self and n.alive and distance(self.pos, n.pos) < 90 and n.health < 200:
                    n.health = min(n.health + 28, 220)
                    self.heal_cd = 5.0
                    break
        super().behavior_engage(dt)
