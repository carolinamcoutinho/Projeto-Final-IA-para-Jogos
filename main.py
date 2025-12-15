# main.py
import pygame, sys
from world import World
from player import Player
from hud import draw_hud
from config import VIEW_W, VIEW_H, FPS, NPC_COUNT, MAP_W, MAP_H, DETECTION_RANGE, NPC_FOV_DEG
from npc import Brute, Shooter, Support
import random
import math
import os

pygame.init()
screen = pygame.display.set_mode((VIEW_W, VIEW_H))
pygame.display.set_caption("Grupo de Inimigos - Protótipo")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "sprites")

def load_sprite(name, size):
    img = pygame.image.load(os.path.join(ASSETS_DIR, name)).convert_alpha()
    return pygame.transform.smoothscale(img, (size, size))


NPC_SIZE = 36   # ajuste fino aqui
PLAYER_SIZE = 40

SPRITES = {
    "Brute": load_sprite("brute.png", NPC_SIZE),
    "Shooter": load_sprite("shooter.png", NPC_SIZE),
    "Support": load_sprite("support.png", NPC_SIZE),
    "Player": load_sprite("player.png", PLAYER_SIZE),
}


# create world and player
world = World(VIEW_W, VIEW_H)
player = Player(world)
world.add_player(player)
world.spawn_group(NPC_COUNT)

camx, camy = player.pos[0], player.pos[1]

def world_to_screen(px, py, camx, camy):
    return int(px - camx + VIEW_W//2), int(py - camy + VIEW_H//2)

def ray_hit_distance(world, origin, angle, max_dist, step=8):
    """Retorna a distância até o primeiro obstáculo ao longo do raio. Se não bater, retorna max_dist."""
    ox, oy = origin
    dx = math.cos(angle)
    dy = math.sin(angle)

    d = 0.0
    while d <= max_dist:
        x = ox + dx * d
        y = oy + dy * d
        if world.point_in_obstacle((x, y)):
            return d
        d += step
    return max_dist


def draw_fov_pretty(screen, world, npc, camx, camy, show_los=True):
    """Cone de visão: verde (visível) + vermelho (ocluído atrás de obstáculo)."""
    if not npc.alive:
        return

    # origem (mundo) e (tela)
    ox, oy = npc.pos[0], npc.pos[1]
    sx, sy = world_to_screen(ox, oy, camx, camy)

    # direção do npc
    fx, fy = getattr(npc, "facing", (1.0, 0.0))
    ang0 = math.atan2(fy, fx)

    # parâmetros
    r = float(DETECTION_RANGE)
    half = math.radians(NPC_FOV_DEG) * 0.5
    rays = 26  # mais = mais bonito, mais pesado

    hit_pts = []
    full_pts = []

    for i in range(rays + 1):
        a = ang0 - half + (2 * half) * (i / rays)
        hit_d = ray_hit_distance(world, (ox, oy), a, r, step=8)

        hx = ox + math.cos(a) * hit_d
        hy = oy + math.sin(a) * hit_d
        fxp = ox + math.cos(a) * r
        fyp = oy + math.sin(a) * r

        hit_pts.append(world_to_screen(hx, hy, camx, camy))
        full_pts.append(world_to_screen(fxp, fyp, camx, camy))

    # desenha em uma surface com alpha
    overlay = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)

    # ✅ parte visível (verde): centro + pontos até onde bate
    green_poly = [(sx, sy)] + hit_pts
    pygame.draw.polygon(overlay, (0, 255, 80, 50), green_poly)

    # ✅ parte ocluída (vermelho): “anel” entre hit_pts e full_pts
    # polígono fechado: full_pts + reversed(hit_pts)
    red_poly = full_pts + list(reversed(hit_pts))
    pygame.draw.polygon(overlay, (255, 60, 60, 45), red_poly)

    # bordas
    pygame.draw.lines(overlay, (0, 255, 80, 120), False, hit_pts, 2)

    screen.blit(overlay, (0, 0))

    # ✅ linha até o player: verde se vê, vermelho se não vê
    if show_los:
        try:
            psx, psy = world_to_screen(world.player.pos[0], world.player.pos[1], camx, camy)
            col = (0, 255, 80) if npc.can_see_player() else (255, 60, 60)
            pygame.draw.line(screen, col, (sx, sy), (psx, psy), 2)
        except Exception:
            pass


def draw_npc_fov(screen, n, camx, camy):
    # posição do NPC na tela
    sx, sy = world_to_screen(n.pos[0], n.pos[1], camx, camy)

    # alcance (círculo)
    pygame.draw.circle(screen, (90, 90, 120), (sx, sy), int(DETECTION_RANGE), 1)

    # direção (facing)
    fx, fy = getattr(n, "facing", [1.0, 0.0])
    ang = math.atan2(fy, fx)
    half = math.radians(NPC_FOV_DEG) * 0.5

    # bordas do cone
    a1 = ang - half
    a2 = ang + half
    r = DETECTION_RANGE

    x1 = sx + int(math.cos(a1) * r)
    y1 = sy + int(math.sin(a1) * r)
    x2 = sx + int(math.cos(a2) * r)
    y2 = sy + int(math.sin(a2) * r)

    # cor muda se vê o player
    seeing = False
    try:
        seeing = n.can_see_player()
    except Exception:
        seeing = False

    col = (0, 220, 120) if seeing else (140, 140, 180)
    pygame.draw.line(screen, col, (sx, sy), (x1, y1), 2)
    pygame.draw.line(screen, col, (sx, sy), (x2, y2), 2)

    # linha do centro (opcional)
    cx = sx + int(math.cos(ang) * (r * 0.5))
    cy = sy + int(math.sin(ang) * (r * 0.5))
    pygame.draw.line(screen, col, (sx, sy), (cx, cy), 2)


def game_reset():
    global world, player, camx, camy
    world = World(VIEW_W, VIEW_H)
    player = Player(world)
    world.add_player(player)
    world.spawn_group(NPC_COUNT)
    camx, camy = player.pos[0], player.pos[1]

running = True
game_over = False

while running:
    dt = clock.tick(FPS) / 1000.0
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pos()

    # Update only when not game over
    if player.alive:
        player.update(dt, keys, mouse, camx, camy)
        world.update(dt)
    else:
        # show game over
        screen.fill((8,8,8))
        font = pygame.font.SysFont(None, 64)
        t1 = font.render("GAME OVER", True, (255,60,60))
        t2 = pygame.font.SysFont(None, 28).render("Pressione R para reiniciar", True, (255,255,255))
        screen.blit(t1, (VIEW_W//2 - t1.get_width()//2, VIEW_H//2 - 40))
        screen.blit(t2, (VIEW_W//2 - t2.get_width()//2, VIEW_H//2 + 20))
        pygame.display.flip()
        if keys[pygame.K_r]:
            game_reset()
        # skip drawing rest
        continue

    # camera follow (clamped)
    camx = max(VIEW_W//2, min(player.pos[0], MAP_W - VIEW_W//2))
    camy = max(VIEW_H//2, min(player.pos[1], MAP_H - VIEW_H//2))

    # draw background
    screen.fill((18,18,28))

    # draw debug grid
    TILE = world.tile
    start_tx = int((camx - VIEW_W//2) // TILE)
    start_ty = int((camy - VIEW_H//2) // TILE)
    tiles_x = VIEW_W // TILE + 3
    tiles_y = VIEW_H // TILE + 3
    for ix in range(start_tx, start_tx + tiles_x):
        for iy in range(start_ty, start_ty + tiles_y):
            sx = ix*TILE - camx + VIEW_W//2
            sy = iy*TILE - camy + VIEW_H//2
            rect = pygame.Rect(int(sx), int(sy), TILE, TILE)
            # draw lightly
            pygame.draw.rect(screen, (22,22,30), rect, 1)

    # draw obstacles
    for r in world.obstacles:
        sx, sy = world_to_screen(r.x, r.y, camx, camy)
        pygame.draw.rect(screen, (60,60,80), (sx, sy, r.width, r.height))

    # draw hearts
    for hx, hy in world.hearts:
        sx, sy = world_to_screen(hx, hy, camx, camy)
        pygame.draw.circle(screen, (255,60,120), (sx, sy), 8)

    # draw projectiles
    for p in world.projectiles:
        sx, sy = world_to_screen(p.pos[0], p.pos[1], camx, camy)
        pygame.draw.circle(screen, (255,200,60), (sx, sy), 4)

    # draw NPCs
    font = pygame.font.SysFont(None, 14)
    for n in world.npcs:
        sx, sy = world_to_screen(n.pos[0], n.pos[1], camx, camy)
        if not n.alive:
            pygame.draw.circle(screen, (70,70,70), (sx, sy), n.radius)
            continue
        draw_fov_pretty(screen, world, n, camx, camy, show_los=True)
        color = getattr(n.__class__, "COLOR", (200,60,60))
        state_name = n.fsm.current.__class__.__name__ if n.fsm.current else "?"
        outline = (0,180,0) if state_name == "Patrol" else (255,255,0) if state_name == "Engage" else (120,180,255) if state_name == "Search" else (255,80,80)

        sprite = SPRITES[n.__class__.__name__]

        # rotaciona conforme a direção (facing)
        fx, fy = getattr(n, "facing", (1, 0))
        angle = -math.degrees(math.atan2(fy, fx))

        img = pygame.transform.rotate(sprite, angle)
        rect = img.get_rect(center=(sx, sy))
        screen.blit(img, rect.topleft)
        pygame.draw.circle(screen, outline, (sx, sy), n.radius, 2)

        # HP bar
        w = 34
        hx = sx - w//2
        hy = sy - n.radius - 12
        pygame.draw.rect(screen, (30,30,30), (hx, hy, w, 5))
        pct = max(0.0, min(1.0, n.health / 220.0))
        pygame.draw.rect(screen, (0,200,0), (hx, hy, int(w*pct), 5))
        txt = font.render(state_name, True, (200,200,200))
        screen.blit(txt, (sx - txt.get_width()//2, hy - 16))


    # draw player
    psx, psy = world_to_screen(player.pos[0], player.pos[1], camx, camy)

    mx, my = mouse  # mouse já está em coordenadas de tela
    dx = mx - psx
    dy = my - psy

    # ângulo em graus (pygame.rotate usa graus; sinal negativo por causa do eixo Y da tela)
    angle = -math.degrees(math.atan2(dy, dx))

    img = SPRITES["Player"]
    rot = pygame.transform.rotate(img, angle)
    rect = rot.get_rect(center=(psx, psy))
    screen.blit(rot, rect.topleft)

    # HUD
    draw_hud(screen, world, player)

    pygame.display.flip()

pygame.quit()
sys.exit()
