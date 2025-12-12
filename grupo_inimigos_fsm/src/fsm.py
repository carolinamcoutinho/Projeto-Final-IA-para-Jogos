class State:
    def enter(self, npc):
        pass

    def execute(self, npc):
        pass

    def exit(self, npc):
        pass

class PatrolState(State):
    def enter(self, npc):
        print(f"{npc.name} está patrulhando.")

    def execute(self, npc):
        # Lógica de patrulha
        print(f"{npc.name} patrulhando...")
        if npc.detecta_jogador():
            npc.change_state(AttackState())

    def exit(self, npc):
        print(f"{npc.name} deixa de patrulhar.")

class AttackState(State):
    def enter(self, npc):
        print(f"{npc.name} atacando o jogador.")

    def execute(self, npc):
        # Lógica de ataque
        print(f"{npc.name} atacando...")
        if not npc.jogador_ao_redor():
            npc.change_state(PatrolState())

    def exit(self, npc):
        print(f"{npc.name} deixa de atacar.")

class RetreatState(State):
    def enter(self, npc):
        print(f"{npc.name} recuando.")

    def execute(self, npc):
        # Lógica de recuo
        print(f"{npc.name} recuando...")
        if npc.is_seguro():
            npc.change_state(PatrolState())

    def exit(self, npc):
        print(f"{npc.name} para de recuar.")
