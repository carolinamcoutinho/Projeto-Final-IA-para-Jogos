# main.py
import pygame, sys
from world import World
from player import Player
from hud import draw_hud
from config import VIEW_W, VIEW_H, FPS, NPC_COUNT, MAP_W, MAP_H
from npc import Brute, Shooter, Support
import random

pygame.init()
screen = pygame.display.set_mode((VIEW_W, VIEW_H))
pygame.display.set_caption("Grupo de Inimigos - Protótipo")
clock = pygame.time.Clock()

# create world and player
world = World(VIEW_W, VIEW_H)
player = Player(world)
world.add_player(player)
world.spawn_group(NPC_COUNT)

camx, camy = player.pos[0], player.pos[1]

def world_to_screen(px, py, camx, camy):
    return int(px - camx + VIEW_W//2), int(py - camy + VIEW_H//2)

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
        color = getattr(n.__class__, "COLOR", (200,60,60))
        state_name = n.fsm.current.__class__.__name__ if n.fsm.current else "?"
        outline = (0,180,0) if state_name == "Patrol" else (255,255,0) if state_name == "Engage" else (255,80,80)
        pygame.draw.circle(screen, color, (sx, sy), n.radius)
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
    pygame.draw.circle(screen, (50,160,255), (psx, psy), player.radius)

    # HUD
    draw_hud(screen, world, player)

    pygame.display.flip()

pygame.quit()
sys.exit()
