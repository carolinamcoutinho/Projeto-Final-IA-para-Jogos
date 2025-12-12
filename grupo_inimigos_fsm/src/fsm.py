# fsm.py
class State:
    def enter(self, npc): pass
    def execute(self, npc, dt): pass
    def exit(self, npc): pass

class FSM:
    def __init__(self, owner):
        self.owner = owner
        self.current = None
    def change(self, new_state):
        if self.current:
            self.current.exit(self.owner)
        self.current = new_state
        if self.current:
            self.current.enter(self.owner)
    def update(self, dt):
        if self.current:
            self.current.execute(self.owner, dt)

# Concrete states
class Patrol(State):
    def enter(self, npc):
        npc.pick_patrol_target()
    def execute(self, npc, dt):
        npc.behavior_patrol(dt)
        if npc.can_see_player():
            npc.world.broadcast_engage()

class Engage(State):
    def execute(self, npc, dt):
        npc.behavior_engage(dt)
        if npc.health <= 0 and npc.alive:
            npc.world.broadcast_retreat()
            npc.fsm.change(Dead())

class Retreat(State):
    def enter(self, npc):
        npc.retreat_timer = 2.5
    def execute(self, npc, dt):
        npc.behavior_retreat(dt)
        npc.retreat_timer -= dt
        if npc.retreat_timer <= 0:
            npc.fsm.change(Patrol())

class Dead(State):
    def enter(self, npc):
        npc.alive = False
