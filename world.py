# world.py
import pygame
import random
from utils import distance
from projectile import Projectile
from config import MAP_W, MAP_H, NPC_RADIUS
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
        self.hearts = []

        # obstáculos (o seu preset atual)
        self.obstacles = [
            pygame.Rect(300, 120, 160, 120),
            pygame.Rect(120, 380, 220, 100),
            pygame.Rect(680, 260, 180, 160),
            pygame.Rect(480, 480, 220, 100),
        ]

        # grid p/ A*
        self.grid = [[0 for _ in range(self.grid_h)] for _ in range(self.grid_w)]
        self._build_grid()

        # spawn hearts
        self.spawn_hearts(5)

    def clamp_to_bounds(self, pos, radius):
        # pos é [x, y]
        pos[0] = max(radius, min(pos[0], self.map_w - radius))
        pos[1] = max(radius, min(pos[1], self.map_h - radius))

    
    # -----------------------
    # GRID (A*)
    # -----------------------
    def _build_grid(self):
        # zera grid
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                self.grid[x][y] = 0

        # marca tiles bloqueados
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                cx = x * self.tile + self.tile / 2
                cy = y * self.tile + self.tile / 2
                for r in self.obstacles:
                    if r.collidepoint(cx, cy):
                        self.grid[x][y] = 1
                        break

    # -----------------------
    # COLISÃO (ponto e círculo)
    # -----------------------
    def point_in_obstacle(self, pt):
        x, y = pt
        for r in self.obstacles:
            if r.collidepoint(x, y):
                return True
        return False

    def circle_in_obstacle(self, pt, radius, margin=0):
        """
        True se o círculo (centro=pt) encosta/entra em algum obstáculo.
        Aproximação rápida: infla o retângulo pelo (radius+margin) e testa o centro.
        """
        x, y = pt
        pad = int(radius + margin)
        for r in self.obstacles:
            if r.inflate(pad * 2, pad * 2).collidepoint(x, y):
                return True
        return False

    def is_free_pos(self, pt, radius, margin=0):
        x, y = pt
        # dentro do mapa considerando raio
        if x < radius + 1 or y < radius + 1:
            return False
        if x > self.map_w - radius - 1 or y > self.map_h - radius - 1:
            return False
        # longe de obstáculo
        return not self.circle_in_obstacle((x, y), radius, margin=margin)

    def find_free_pos(self, radius, attempts=600, margin=6):
        for _ in range(attempts):
            x = random.randint(int(radius + 10), int(self.map_w - radius - 10))
            y = random.randint(int(radius + 10), int(self.map_h - radius - 10))
            if self.is_free_pos((x, y), radius, margin=margin):
                return [float(x), float(y)]
        return [self.map_w / 2, self.map_h / 2]

    # -----------------------
    # PLAYER / NPC / ITEMS SPAWN
    # -----------------------
    def add_player(self, player):
        self.player = player
        pr = getattr(player, "radius", 16)
        if self.circle_in_obstacle(player.pos, pr, margin=4):
            player.pos = self.find_free_pos(pr, margin=6)

    def spawn_hearts(self, count):
        heart_r = 10
        for _ in range(count):
            pos = self.find_free_pos(heart_r, attempts=500, margin=4)
            self.hearts.append([pos[0], pos[1]])

    def spawn_group(self, count):
        for _ in range(count):
            typ = random.choice([Brute, Shooter, Support])
            r = getattr(typ, "RADIUS", NPC_RADIUS)
            pos = self.find_free_pos(r, attempts=700, margin=6)
            self.npcs.append(typ(self, pos[0], pos[1]))

    # -----------------------
    # PROJÉTEIS / UPDATE
    # -----------------------
    def spawn_projectile(self, pos, vel, dmg=10, owner=None):
        self.projectiles.append(Projectile(pos[:], vel[:], dmg, owner))

    def update(self, dt):
        for n in self.npcs:
            n.update(dt)

        for p in list(self.projectiles):
            alive = p.update(dt, self)
            if not alive:
                try:
                    self.projectiles.remove(p)
                except ValueError:
                    pass

        for h in list(self.hearts):
            if distance(self.player.pos, h) < 26:
                self.player.hp = min(self.player.max_hp, self.player.hp + 40)
                self.hearts.remove(h)

    # -----------------------
    # IA de grupo (fsm.py chama isso)
    # -----------------------
    def alert_engage(self, spotter):
        if not getattr(spotter, "alive", False):
            return

        if getattr(spotter, "last_seen_pos", None) is None:
            spotter.last_seen_pos = self.player.pos[:]

        for n in self.npcs:
            if (not n.alive) or (n is spotter):
                continue
            if distance(spotter.pos, n.pos) < 280:
                n.last_seen_pos = spotter.last_seen_pos[:]
                n.time_since_seen = 0.0
                cur = n.fsm.current.__class__.__name__ if n.fsm.current else ""
                if cur not in ("Engage", "Dead"):
                    n.fsm.change(self.engage_state())

    # -----------------------
    # A*
    # -----------------------
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

            for dx, dy in dirs:
                nb = (current[0]+dx, current[1]+dy)
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
