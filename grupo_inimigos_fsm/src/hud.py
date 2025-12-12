import pygame

def draw_hud(screen, world, player):
    font = pygame.font.SysFont(None, 20)

    # Background panel
    pygame.draw.rect(screen, (20,20,20), (8,8,240,90))

    # Player HP
    hp_text = font.render(f"HP: {int(player.hp)}", True, (255,255,255))
    screen.blit(hp_text, (16, 16))

    # Cooldowns
    dash_text = font.render(f"Dash CD: {player.dash_cd:.1f}", True, (200,200,200))
    emp_text = font.render(f"EMP CD: {player.emp_cd:.1f}", True, (200,200,200))
    shoot_text = font.render(f"Shoot CD: {player.shoot_cd:.2f}", True, (200,200,200))

    screen.blit(dash_text, (16, 36))
    screen.blit(emp_text, (16, 56))
    screen.blit(shoot_text, (16, 76))
