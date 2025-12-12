# main.py
import pygame, sys
from world import World
from player import Player
from hud import draw_hud
from config import VIEW_W, VIEW_H, FPS, NPC_COUNT, MAP_W, MAP_H, TILE

pygame.init()
screen = pygame.display.set_mode((VIEW_W, VIEW_H))
pygame.display.set_caption("Grupo de Inimigos: FSM + Steering + A* (Protótipo)")
clock = pygame.time.Clock()

world = World(VIEW_W, VIEW_H)
player = Player(world)
world.add_player(player)
world.spawn_group(NPC_COUNT)

camx, camy = player.pos[0], player.pos[1]

def world_to_screen(px, py, camx, camy):
    return int(px - camx + VIEW_W//2), int(py - camy + VIEW_H//2)

running = True
while running:
    dt = clock.tick(FPS)/1000.0
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pos()

    # update
    player.update(dt, keys, mouse, camx, camy)
    world.update(dt)

    # camera follows player but clamped to map bounds
    camx = max(VIEW_W//2, min(player.pos[0], MAP_W - VIEW_W//2))
    camy = max(VIEW_H//2, min(player.pos[1], MAP_H - VIEW_H//2))

    # draw background
    screen.fill((18,18,30))

    # draw grid/tiles lightly for debugging
    start_tx = int((camx - VIEW_W//2) // TILE)
    start_ty = int((camy - VIEW_H//2) // TILE)
    tiles_x = VIEW_W // TILE + 3
    tiles_y = VIEW_H // TILE + 3
    for ix in range(start_tx, start_tx + tiles_x):
        for iy in range(start_ty, start_ty + tiles_y):
            sx = ix * TILE - camx + VIEW_W//2
            sy = iy * TILE - camy + VIEW_H//2
            rect = pygame.Rect(int(sx), int(sy), TILE, TILE)
            if 0 <= ix < world.grid_w and 0 <= iy < world.grid_h and world.grid[ix][iy] == 1:
                pygame.draw.rect(screen, (40,40,50), rect)
            else:
                pygame.draw.rect(screen, (20,20,28), rect, 1)

    # obstacles
    for r in world.obstacles:
        sx,sy = world_to_screen(r.x, r.y, camx, camy)
        rr = pygame.Rect(sx, sy, r.width, r.height)
        pygame.draw.rect(screen, (60,60,70), rr)

    # projectiles
    for p in world.projectiles:
        sx,sy = world_to_screen(p.pos[0], p.pos[1], camx, camy)
        pygame.draw.circle(screen, (255,200,40), (sx,sy), 4)

    # NPCs
    for n in world.npcs:
        sx,sy = world_to_screen(n.pos[0], n.pos[1], camx, camy)
        if not n.alive:
            pygame.draw.circle(screen, (70,70,70), (sx,sy), n.radius)
            continue
        color = getattr(n.__class__, "COLOR", (200,60,60))
        # state color overlay
        state_name = n.fsm.current.__class__.__name__ if n.fsm.current else "?"
        if state_name == "Patrol":
            outline = (0,200,0)
        elif state_name == "Engage":
            outline = (220,200,0)
        else:
            outline = (200,70,70)
        pygame.draw.circle(screen, color, (sx,sy), n.radius)
        pygame.draw.circle(screen, outline, (sx,sy), n.radius, 2)
        # health bar above
        w = 32
        hx = sx - w//2
        hy = sy - n.radius - 10
        pygame.draw.rect(screen, (40,40,40), (hx, hy, w, 5))
        hpw = int(w * max(0.0, min(1.0, n.health / 220.0)))
        pygame.draw.rect(screen, (0,200,0), (hx, hy, hpw, 5))
        # small text state
        font = pygame.font.SysFont(None, 16)
        txt = font.render(state_name, True, (200,200,200))
        screen.blit(txt, (sx - txt.get_width()//2, hy - 16))

    # player
    psx,psy = world_to_screen(player.pos[0], player.pos[1], camx, camy)
    pygame.draw.circle(screen, (50,150,255), (psx,psy), player.radius)
    # small player hp (not tracked separately in this prototype)
    # draw HUD
    draw_hud(screen, world, player)

    pygame.display.flip()

pygame.quit()
sys.exit()
