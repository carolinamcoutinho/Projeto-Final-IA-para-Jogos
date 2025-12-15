class State:
    def enter(self, npc):
        pass
    def exit(self, npc):
        pass
    def update(self, npc, dt):
        pass


class Patrol(State):
    def enter(self, npc):
        # ensure a target exists
        if npc.patrol_target is None:
            npc.pick_patrol_target()

    def update(self, npc, dt):
        npc.behavior_patrol(dt)
        if npc.can_see_player():
            npc.world.alert_engage(spotter=npc)
            npc.fsm.change(Engage())


class Engage(State):
    def enter(self, npc):
        npc.search_timer = 0.0

    def update(self, npc, dt):
        # primeiro executa o combate (isso atualiza time_since_seen / last_seen_pos)
        npc.behavior_engage(dt)

        # só considera "perdeu" depois de um tempo
        LOST_SIGHT_GRACE = 0.70  # segundos (ajuste 0.4–1.2)
        if npc.last_seen_pos is not None and npc.time_since_seen > LOST_SIGHT_GRACE:
            npc.fsm.change(Search())
            return

        if npc.health < 20:
            npc.fsm.change(Retreat())



class Search(State):
    def enter(self, npc):
        npc.search_timer = 0.0
        # per-search timeout (adds variety)
        npc.search_timeout = npc.search_timeout_base

    def update(self, npc, dt):
        npc.search_timer += dt

        if npc.can_see_player():
            npc.world.alert_engage(spotter=npc)
            npc.fsm.change(Engage())
            return

        npc.behavior_search(dt)

        # give up after a while
        if npc.search_timer >= npc.search_timeout:
            npc.fsm.change(Patrol())


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
