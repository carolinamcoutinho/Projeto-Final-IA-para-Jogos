class State:
    def enter(self, npc): pass
    def exit(self, npc): pass
    def update(self, npc, dt): pass

class Patrol(State):
    def update(self, npc, dt):
        npc.behavior_patrol(dt)
        if npc.can_see_player():
            npc.fsm.change(Engage())

class Engage(State):
    def update(self, npc, dt):
        npc.behavior_engage(dt)
        if npc.health < 30:
            npc.fsm.change(Retreat())

class Retreat(State):
    def update(self, npc, dt):
        npc.behavior_retreat(dt)
        if npc.health > 70:
            npc.fsm.change(Patrol())

class Dead(State):
    pass

class FSM:
    def __init__(self, npc):
        self.npc = npc
        self.current = None

    def change(self, new_state):
        if self.current:
            self.current.exit(self.npc)
        self.current = new_state
        self.current.enter(self.npc)

    def update(self, dt):
        if self.current:
            self.current.update(self.npc, dt)
