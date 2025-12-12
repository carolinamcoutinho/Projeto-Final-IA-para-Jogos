# world.py
import pygame
import random
from utils import distance
from projectile import Projectile
from config import MAP_W, MAP_H, VIEW_W, VIEW_H

# NPC classes imported dynamically to avoid circular import issues
from npc import Brute, Shooter, Support
from fsm import Retreat, Engage, Patrol

class World:
    def __init__(self, view_w, view_h):
        self.map_w = MAP_W
        self.map_h = MAP_H
        self.view_w = view_w
        self.view_h = view_h

        self.tile = 32
        self.grid_w = self.map_w // self.tile
        self.grid_h = self.map_h // self.tile

        self.npcs = []
        self.projectiles = []
        self.obstacles = []
        self.hearts = []

        # parameters for EMP (accessible via player/world)
        self.emp_radius = 140
        self.emp_damage = 20
        self.emp_knockback = 220

        # define obstacles
        self.obstacles = [
            pygame.Rect(300, 120, 160, 120),
            pygame.Rect(120, 380, 220, 100),
            pygame.Rect(680, 260, 180, 160),
            pygame.Rect(480, 480, 220, 100)
        ]

        # build grid
        self.grid = [[0 for _ in range(self.grid_h)] for _ in range(self.grid_w)]
        self._build_grid()

        # spawn hearts
        self.spawn_hearts(5)

    def _build_grid(self):
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                cx = x * self.tile + self.tile / 2
                cy = y * self.tile + self.tile / 2
                for r in self.obstacles:
                    if r.collidepoint(cx, cy):
                        self.grid[x][y] = 1
                        break

    def point_in_obstacle(self, pt):
        x, y = pt
        for r in self.obstacles:
            if r.collidepoint(x, y):
                return True
        return False

    def add_player(self, player):
        self.player = player

    def spawn_hearts(self, count):
        for _ in range(count):
            placed = False
            attempts = 0
            while not placed and attempts < 400:
                attempts += 1
                x = random.randint(40, self.map_w - 40)
                y = random.randint(40, self.map_h - 40)
                if not self.point_in_obstacle((x, y)):
                    self.hearts.append([x, y])
                    placed = True

    def spawn_group(self, count):
        for i in range(count):
            placed = False
            attempts = 0
            while not placed and attempts < 300:
                attempts += 1
                x = random.randint(60, self.map_w - 60)
                y = random.randint(60, self.map_h - 60)
                if not self.point_in_obstacle((x, y)):
                    typ = random.choice([Brute, Shooter, Support])
                    self.npcs.append(typ(self, x, y))
                    placed = True
            if not placed:
                # fallback
                self.npcs.append(Shooter(self, 100 + i*20, 100))

    def broadcast_engage(self):
        for n in self.npcs:
            if n.alive:
                n.fsm.change(Engage())

    def broadcast_retreat(self):
        for n in self.npcs:
            if n.alive:
                n.fsm.change(Retreat())

    def spawn_projectile(self, pos, vel, dmg=10, owner=None):
        self.projectiles.append(Projectile(pos[:], vel[:], dmg, owner))

    def update(self, dt):
        # update NPCs
        for n in self.npcs:
            n.update(dt)

        # update projectiles (iterate copy)
        for p in list(self.projectiles):
            alive = p.update(dt, self)
            if not alive:
                try:
                    self.projectiles.remove(p)
                except ValueError:
                    pass

        # heart pickup
        for h in list(self.hearts):
            if distance(self.player.pos, h) < 26:
                self.player.hp = min(self.player.max_hp, self.player.hp + 40)
                self.hearts.remove(h)

    # A* implementation
    def astar(self, start, goal):
        sx, sy = start
        gx, gy = goal
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return None
        if self.grid[gx][gy] == 1:
            return None

        import heapq
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]

        def h(a,b):
            return abs(a[0]-b[0]) + abs(a[1]-b[1])

        openh = []
        heapq.heappush(openh, (0, (sx, sy)))
        came = {(sx, sy): None}
        gscore = {(sx, sy): 0}

        while openh:
            _, current = heapq.heappop(openh)
            if current == (gx, gy):
                path = []
                n = current
                while n:
                    path.append(n)
                    n = came[n]
                path.reverse()
                return path
            for d in dirs:
                nb = (current[0]+d[0], current[1]+d[1])
                x, y = nb
                if x < 0 or y < 0 or x >= self.grid_w or y >= self.grid_h:
                    continue
                if self.grid[x][y] == 1:
                    continue
                tentative = gscore[current] + 1
                if nb not in gscore or tentative < gscore[nb]:
                    gscore[nb] = tentative
                    pri = tentative + h(nb, (gx, gy))
                    heapq.heappush(openh, (pri, nb))
                    came[nb] = current
        return None

    def retreat_state(self):
        return Retreat()

    def engage_state(self):
        return Engage()

    def patrol_state(self):
        return Patrol()

    def on_player_death(self):
        print("PLAYER MORREU!")
        # could add more: game over screen handled in main.py
