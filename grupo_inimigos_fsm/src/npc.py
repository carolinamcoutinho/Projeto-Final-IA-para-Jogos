# npc.py
import random, time
from utils import distance, normalize, sub, add, mul
from steering import seek, separation, cohesion, alignment, flee
from fsm import FSM, Patrol, Engage, Retreat, Dead
from config import NPC_MAX_SPEED, NPC_RADIUS, CHARGE_COOLDOWN, CHARGE_SPEED, PATH_REPLAN_INTERVAL, DETECTION_RANGE, ATTACK_RANGE, STEER_SEPARATION, STEER_COHESION, STEER_ALIGNMENT

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

        # path following
        self.path = None
        self.path_idx = 0
        self.next_replan = 0.0

    def pick_patrol_target(self):
        self.patrol_target = [random.randint(60, self.world.map_w-60), random.randint(60, self.world.map_h-60)]

    def neighbors(self):
        return [n for n in self.world.npcs if n is not self and n.alive and distance(self.pos, n.pos) < 120]

    def can_see_player(self):
        # simple distance check + line of sight (no raycast for now)
        return distance(self.pos, self.world.player.pos) < DETECTION_RANGE

    # ---------- behaviors ----------
    def behavior_patrol(self, dt):
        if distance(self.pos, self.patrol_target) < 12:
            self.pick_patrol_target()
        desired = seek(self.pos, self.patrol_target, self.max_speed*0.45)
        self.apply_force(desired, dt)

    def behavior_engage(self, dt):
        player_pos = self.world.player.pos
        neigh = self.neighbors()

        s = separation(self, neigh)
        c = cohesion(self, neigh)
        a = alignment(self, neigh)
        sk = seek(self.pos, player_pos, self.max_speed)

        force = [sk[0] + s[0]*STEER_SEPARATION + c[0]*STEER_COHESION + a[0]*STEER_ALIGNMENT,
                 sk[1] + s[1]*STEER_SEPARATION + c[1]*STEER_COHESION + a[1]*STEER_ALIGNMENT]

        # pathfinding: if obstacle between and grid exists, follow path
        # replan periodically
        self.next_replan -= dt
        if self.path is None or self.next_replan <= 0:
            self.plan_path_to(player_pos)
            self.next_replan = PATH_REPLAN_INTERVAL

        # follow path if exists
        if self.path:
            # target waypoint
            if self.path_idx < len(self.path):
                wp = self.path[self.path_idx]
                # wp is tile index center to world coords
                targ = [wp[0]*self.world.tile + self.world.tile/2, wp[1]*self.world.tile + self.world.tile/2]
                if distance(self.pos, targ) < 10:
                    self.path_idx += 1
                else:
                    pseek = seek(self.pos, targ, self.max_speed)
                    force = [pseek[0] + s[0]*STEER_SEPARATION + a[0]*STEER_ALIGNMENT,
                             pseek[1] + s[1]*STEER_SEPARATION + a[1]*STEER_ALIGNMENT]

        # charge ability (basic)
        if self.charge_cd <= 0 and distance(self.pos, player_pos) > 70:
            self.vel = mul(normalize(sub(player_pos, self.pos)), CHARGE_SPEED)
            self.charge_cd = CHARGE_COOLDOWN
        else:
            self.apply_force(force, dt)

        self.charge_cd = max(0.0, self.charge_cd - dt)

    def behavior_retreat(self, dt):
        player_pos = self.world.player.pos
        f = flee(self.pos, player_pos, self.max_speed*0.8)
        self.apply_force(f, dt)

    def apply_force(self, desired_vel, dt):
        # simple velocity smoothing
        self.vel[0] += (desired_vel[0] - self.vel[0]) * (1.0 * dt * 6.0)
        self.vel[1] += (desired_vel[1] - self.vel[1]) * (1.0 * dt * 6.0)
        # clamp
        spd = (self.vel[0]**2 + self.vel[1]**2)**0.5
        if spd > self.max_speed:
            scale = self.max_speed / spd
            self.vel[0] *= scale; self.vel[1] *= scale
        # move and obstacle collision simple
        newx = self.pos[0] + self.vel[0]*dt
        newy = self.pos[1] + self.vel[1]*dt
        if not self.world.point_in_obstacle((newx, newy)):
            self.pos[0] = newx; self.pos[1] = newy
        else:
            # simple slide: stop velocity when hitting obstacle
            self.vel = [0.0, 0.0]

    def update(self, dt):
        if not self.alive: return
        self.fsm.update(dt)
        if self.health <= 0 and self.alive:
            # death explosion: small push and broadcast retreat
            self.alive = False
            for oth in self.world.npcs:
                if oth.alive:
                    oth.fsm.change(self.world.retreat_state())
            # mark as dead; world will keep it visually

    # ---------- pathfinding ----------
    def plan_path_to(self, world_pos):
        # convert world_pos to tile coords
        tx = int(world_pos[0] // self.world.tile)
        ty = int(world_pos[1] // self.world.tile)
        sx = int(self.pos[0] // self.world.tile)
        sy = int(self.pos[1] // self.world.tile)
        path = self.world.astar((sx,sy), (tx,ty))
        if path:
            self.path = path
            self.path_idx = 0
        else:
            self.path = None
            self.path_idx = 0
# subclasses with colors & slight stat differences
class Brute(BaseNPC):
    COLOR = (255, 74, 74)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 220
        self.max_speed = 110

class Shooter(BaseNPC):
    COLOR = (255, 229, 93)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 100
        self.max_speed = 150
        self.shoot_cd = 0.0
    def behavior_engage(self, dt):
        # use base engage to path/steer, but shoot projectiles at intervals
        super().behavior_engage(dt)
        self.shoot_cd -= dt
        player_pos = self.world.player.pos
        if self.shoot_cd <= 0 and distance(self.pos, player_pos) < 380:
            dirv = normalize([player_pos[0]-self.pos[0], player_pos[1]-self.pos[1]])
            from projectile import Projectile
            vel = mul(dirv, 440.0)
            self.world.spawn_projectile(self.pos[:], vel, dmg=18, owner=self)
            self.shoot_cd = 0.9

class Support(BaseNPC):
    COLOR = (194, 111, 255)
    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.health = 110
        self.max_speed = 140
        self.heal_cd = 0.0
    def behavior_engage(self, dt):
        # heal nearby allies when possible
        self.heal_cd -= dt
        if self.heal_cd <= 0:
            for n in self.world.npcs:
                if n is not self and n.alive and distance(self.pos, n.pos) < 80 and n.health < 180:
                    n.health = min(220, n.health + 26)
                    self.heal_cd = 5.0
                    break
        super().behavior_engage(dt)
