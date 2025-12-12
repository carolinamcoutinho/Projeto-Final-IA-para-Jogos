import random
from fsm import PatrolState, AttackState, RetreatState
from steering import SteeringBehavior

class NPC:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.state = PatrolState()
        self.steering = SteeringBehavior()

    def change_state(self, new_state):
        self.state.exit(self)
        self.state = new_state
        self.state.enter(self)

    def detecta_jogador(self):
        # Lógica de detecção do jogador
        return random.choice([True, False])

    def jogador_ao_redor(self):
        # Verifica se o jogador está por perto
        return random.choice([True, False])

    def is_seguro(self):
        # Verifica se é seguro voltar a patrulhar
        return random.choice([True, False])

    def update(self):
        self.state.execute(self)
