import pygame
from npc import NPC
from fsm import PatrolState

pygame.init()

# Configurações do jogo
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Grupo de Inimigos com Coordenação")

def game_loop():
    npc1 = NPC("Inimigo 1", (100, 100))
    npc2 = NPC("Inimigo 2", (200, 200))
    npc3 = NPC("Inimigo 3", (300, 300))

    npcs = [npc1, npc2, npc3]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Atualiza todos os NPCs
        for npc in npcs:
            npc.update()

        screen.fill((0, 0, 0))
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    game_loop()
