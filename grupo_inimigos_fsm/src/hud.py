# hud.py
import pygame

def draw_hud(screen, world, player):
    font = pygame.font.SysFont(None, 20)

    # panel
    pygame.draw.rect(screen, (20,20,20), (8,8,260,110))

    # HP text
    hp_text = font.render(f"HP: {int(player.hp)} / {player.max_hp}", True, (255,255,255))
    screen.blit(hp_text, (16, 12))

    # HP bar
    bar_x, bar_y, bar_w, bar_h = 16, 36, 200, 14
    pygame.draw.rect(screen, (40,40,40), (bar_x, bar_y, bar_w, bar_h))
    pct = max(0.0, min(1.0, player.hp / player.max_hp))
    if pct > 0.6:
        color = (0,200,0)
    elif pct > 0.3:
        color = (240,200,0)
    else:
        color = (255,60,60)
    pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w*pct), bar_h))

    # cooldowns
    dash = font.render(f"Dash: {player.dash_cd:.1f}s", True, (200,200,200))
    emp = font.render(f"EMP: {player.emp_cd:.1f}s", True, (200,200,200))
    shoot = font.render(f"Shoot: {player.shoot_cd:.2f}s", True, (200,200,200))
    screen.blit(dash, (16, 56))
    screen.blit(emp, (16, 76))
    screen.blit(shoot, (16, 96))

    alive = sum(1 for n in world.npcs if n.alive)
    txt = font.render(f"Inimigos vivos: {alive}/{len(world.npcs)}", True, (255,255,255))
    screen.blit(txt, (280, 12))
