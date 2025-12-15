# npc.py
import random
import math

from utils import distance, normalize, mul
from steering import seek, separation, cohesion, alignment, flee
from fsm import FSM, Patrol, Engage, Search, Retreat, Dead
from config import (
    NPC_MAX_SPEED, NPC_RADIUS,
    CHARGE_COOLDOWN, CHARGE_SPEED,
    PATH_REPLAN_INTERVAL, DETECTION_RANGE,
    NPC_FOV_DEG
)


class BaseNPC:
    def __init__(self, world, x, y):
        self.world = world
        self.pos = [float(x), float(y)]
        self.vel = [0.0, 0.0]
        self.radius = NPC_RADIUS
        self.health = 100.0
        self.max_speed = NPC_MAX_SPEED
        self.alive = True

        # patrol
        self.patrol_target = None

        # abilities / cooldowns
        self.charge_cd = 0.0

        # perception / memory
        self.facing = [1.0, 0.0]          # direção "pra frente"
        self.last_seen_pos = None         # última posição vista do player
        self.time_since_seen = 999.0      # tempo desde a última visão

        # ✅ Search timers (usado pelo fsm.py)
        self.search_timeout_base = 5.0
        self.search_timeout = self.search_timeout_base
        
        # pathfinding
        self.path = None
        self.path_idx = 0
        self.next_replan = 0.0

        # EMP stun
        self.stunned = 0.0

        # FSM
        self.fsm = FSM(self)
        self.fsm.change(Patrol())

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
        """Perception: range + FOV cone + simple LOS sampling."""
        player = self.world.player
        to_p = [player.pos[0] - self.pos[0], player.pos[1] - self.pos[1]]

        # 1) range
        if (to_p[0] * to_p[0] + to_p[1] * to_p[1]) > (DETECTION_RANGE * DETECTION_RANGE):
            return False

        # 2) FOV cone
        to_p_n = normalize(to_p)
        dotv = self.facing[0] * to_p_n[0] + self.facing[1] * to_p_n[1]
        fov_cos = math.cos(math.radians(NPC_FOV_DEG) * 0.5)
        if dotv < fov_cos:
            return False

        # 3) LOS (line-of-sight) sampling
        steps = 12
        for i in range(1, steps + 1):
            t = i / steps
            x = self.pos[0] + to_p[0] * t
            y = self.pos[1] + to_p[1] * t
            if self.world.point_in_obstacle((x, y)):
                return False

        return True

    # -----------------------
    # BEHAVIORS
    # -----------------------
    def behavior_patrol(self, dt):
        if self.patrol_target is None:
            self.pick_patrol_target()

        # memory update
        if self.can_see_player():
            self.last_seen_pos = self.world.player.pos[:]
            self.time_since_seen = 0.0
        else:
            self.time_since_seen += dt

        if distance(self.pos, self.patrol_target) < 12:
            self.pick_patrol_target()

        desired = seek(self.pos, self.patrol_target, self.max_speed * 0.45)
        self.apply_force(desired, dt)

    def behavior_engage(self, dt):
        if self.stunned > 0:
            self.stunned -= dt
            return

        player_pos = self.world.player.pos

        # memory update
        if self.can_see_player():
            self.last_seen_pos = player_pos[:]
            self.time_since_seen = 0.0
        else:
            self.time_since_seen += dt

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
        if (self.path is None) or (self.next_replan <= 0):
            self.plan_path_to(player_pos)
            self.next_replan = PATH_REPLAN_INTERVAL

        # follow path waypoints if exist
        if self.path and self.path_idx < len(self.path):
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

            # update facing immediately
            if abs(self.vel[0]) + abs(self.vel[1]) > 0.01:
                self.facing = normalize(self.vel)

            self.charge_cd = CHARGE_COOLDOWN
        else:
            self.apply_force(force, dt)

        self.charge_cd = max(0.0, self.charge_cd - dt)

    def behavior_search(self, dt):
        """Go to last seen player position, then sweep around for a bit."""
        if self.stunned > 0:
            self.stunned -= dt
            return

        if self.last_seen_pos is None:
            self.behavior_patrol(dt)
            return

        # if reacquired vision, Engage will be handled by FSM (or you can do it here)
        if self.can_see_player():
            self.last_seen_pos = self.world.player.pos[:]
            self.time_since_seen = 0.0

        # replan sometimes while searching too
        self.next_replan -= dt
        if (self.path is None) or (self.next_replan <= 0):
            self.plan_path_to(self.last_seen_pos)
            self.next_replan = PATH_REPLAN_INTERVAL

        # follow path if we have one
        if self.path and self.path_idx < len(self.path):
            wp = self.path[self.path_idx]
            wx = wp[0] * self.world.tile + self.world.tile / 2
            wy = wp[1] * self.world.tile + self.world.tile / 2

            if distance(self.pos, (wx, wy)) < 10:
                self.path_idx += 1

            desired = seek(self.pos, (wx, wy), self.max_speed * 0.85)
            self.apply_force(desired, dt)
            return

        # if arrived (or no path), do a local sweep
        if distance(self.pos, self.last_seen_pos) < 30:
            ang = random.random() * math.tau
            rad = 60 + random.random() * 90
            sweep = [
                self.last_seen_pos[0] + math.cos(ang) * rad,
                self.last_seen_pos[1] + math.sin(ang) * rad,
            ]
            desired = seek(self.pos, sweep, self.max_speed * 0.7)
        else:
            desired = seek(self.pos, self.last_seen_pos, self.max_speed * 0.85)

        self.apply_force(desired, dt)

    def behavior_retreat(self, dt):
        f = flee(self.pos, self.world.player.pos, self.max_speed * 0.9)
        self.apply_force(f, dt)

    # -----------------------
    # PHYSICS (anti-stuck)
    # -----------------------
    def apply_force(self, desired_vel, dt):
        # velocity smoothing
        self.vel[0] += (desired_vel[0] - self.vel[0]) * dt * 6.0
        self.vel[1] += (desired_vel[1] - self.vel[1]) * dt * 6.0

        # clamp speed
        speed = (self.vel[0] * self.vel[0] + self.vel[1] * self.vel[1]) ** 0.5
        if speed > self.max_speed:
            k = self.max_speed / speed
            self.vel[0] *= k
            self.vel[1] *= k

        # update facing
        if abs(self.vel[0]) + abs(self.vel[1]) > 0.01:
            self.facing = normalize(self.vel)

        newx = self.pos[0] + self.vel[0] * dt
        newy = self.pos[1] + self.vel[1] * dt

        # try full move (usa círculo, não ponto)
        if not self.world.circle_in_obstacle((newx, newy), self.radius, margin=2):
            self.pos[0] = newx
            self.pos[1] = newy
            return

        # slide on X
        if not self.world.circle_in_obstacle((newx, self.pos[1]), self.radius, margin=2):
            self.pos[0] = newx
            self.vel[1] *= 0.35
            return

        # slide on Y
        if not self.world.circle_in_obstacle((self.pos[0], newy), self.radius, margin=2):
            self.pos[1] = newy
            self.vel[0] *= 0.35
            return
        
        # stuck in corner: small random nudge
        ang = random.random() * math.tau
        nx = self.pos[0] + math.cos(ang) * 6
        ny = self.pos[1] + math.sin(ang) * 6
        if not self.world.circle_in_obstacle((nx, ny), self.radius, margin=2):
            self.pos[0] = nx
            self.pos[1] = ny
        self.world.clamp_to_bounds(self.pos, self.radius)
        self.vel = [0.0, 0.0]



    # -----------------------
    # UPDATE + PATHFINDING
    # -----------------------
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
