# world.py
import pygame, random, math
from config import MAP_W, MAP_H, TILE
from npc import Brute, Shooter, Support
from fsm import Retreat, Patrol, Engage, Dead
from projectile import Projectile

class World:
    def __init__(self, view_w, view_h):
        self.map_w = MAP_W
        self.map_h = MAP_H
        self.view_w = view_w
        self.view_h = view_h
        self.tile = TILE
        self.grid_w = self.map_w // self.tile
        self.grid_h = self.map_h // self.tile

        self.npcs = []
        self.projectiles = []
        self.obstacles = []

        # make some rectangular obstacles (simple)
        self.obstacles = [
            pygame.Rect(300,120,160,120),
            pygame.Rect(120,380,220,100),
            pygame.Rect(680,260,180,160),
            pygame.Rect(480,480,220,100)
        ]

        # build grid occupancy from obstacles
        self.grid = [[0 for _ in range(self.grid_h)] for _ in range(self.grid_w)]
        self._build_grid()

    def _build_grid(self):
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                cx = x*self.tile + self.tile/2
                cy = y*self.tile + self.tile/2
                for r in self.obstacles:
                    if r.collidepoint(cx, cy):
                        self.grid[x][y] = 1
                        break

    def add_player(self, player):
        self.player = player

    def spawn_group(self, count):
        # spawn mixed types near top-left area avoiding obstacles
        for i in range(count):
            placed = False
            attempt = 0
            while not placed and attempt < 200:
                attempt += 1
                x = random.randint(60, self.map_w-60)
                y = random.randint(60, self.map_h-60)
                point = (x,y)
                if not self.point_in_obstacle(point):
                    placed = True
                    typ = random.choice([Brute, Shooter, Support])
                    self.npcs.append(typ(self, x, y))
            if not placed:
                self.npcs.append(Shooter(self, 100+i*30, 100))

    def point_in_obstacle(self, pt):
        x,y = pt
        for r in self.obstacles:
            if r.collidepoint(x,y):
                return True
        return False

    # coordinate broadcasts
    def broadcast_engage(self):
        for n in self.npcs:
            if n.alive:
                n.fsm.change(Engage())

    def broadcast_retreat(self):
        for n in self.npcs:
            if n.alive:
                n.fsm.change(Retreat())

    # projectiles
    def spawn_projectile(self, pos, vel, dmg=10, owner=None):
        self.projectiles.append(Projectile(pos[:], vel[:], dmg, owner))

    def update(self, dt):
        # update npcs
        for n in self.npcs:
            n.update(dt)
        # update projectiles
        for p in list(self.projectiles):
            if not p.update(dt, self):
                self.projectiles.remove(p)

    # simple A* (grid) implementation
    def astar(self, start, goal):
        sx,sy = start; gx,gy = goal
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h): return None
        if self.grid[gx][gy] == 1: return None
        import heapq
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        def h(a,b):
            return abs(a[0]-b[0]) + abs(a[1]-b[1])
        openh = []
        heapq.heappush(openh, (0, (sx,sy)))
        came = { (sx,sy): None }
        gscore = { (sx,sy): 0 }
        while openh:
            _, current = heapq.heappop(openh)
            if current == (gx,gy):
                # reconstruct
                path = []
                node = current
                while node:
                    path.append(node)
                    node = came[node]
                path.reverse()
                return path
            for d in dirs:
                nb = (current[0]+d[0], current[1]+d[1])
                x,y = nb
                if x<0 or y<0 or x>=self.grid_w or y>=self.grid_h: continue
                if self.grid[x][y] == 1: continue
                tentative = gscore[current] + 1
                if nb not in gscore or tentative < gscore[nb]:
                    gscore[nb] = tentative
                    pri = tentative + h(nb, (gx,gy))
                    heapq.heappush(openh, (pri, nb))
                    came[nb] = current
        return None

    def retreat_state(self): from fsm import Retreat; return Retreat()
    def flank_state(self): from fsm import Patrol; return Patrol()
    def alert_state(self): from fsm import Engage; return Engage()
