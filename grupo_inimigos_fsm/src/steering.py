# steering.py
from utils import sub, normalize, length, add, mul, div

def seek(pos, target, max_speed):
    desired = sub(target, pos)
    L = length(desired)
    if L == 0: return [0.0, 0.0]
    return mul(desired, max_speed / L)

def flee(pos, target, max_speed):
    desired = sub(pos, target)
    L = length(desired)
    if L == 0: return [0.0, 0.0]
    return mul(desired, max_speed / L)

def separation(npc, neighbors, desired_sep=40):
    steer = [0.0, 0.0]
    count = 0
    for n in neighbors:
        d = length(sub(n.pos, npc.pos))
        if 0 < d < desired_sep:
            diff = sub(n.pos, npc.pos)
            diff = [diff[0]/d, diff[1]/d]
            steer = add(steer, diff)
            count += 1
    if count > 0:
        steer = div(steer, count)
    return steer

def cohesion(npc, neighbors):
    if not neighbors: return [0.0,0.0]
    center = [0.0, 0.0]
    for o in neighbors:
        center = add(center, o.pos)
    center = div(center, len(neighbors))
    return sub(center, npc.pos)

def alignment(npc, neighbors):
    if not neighbors: return [0.0,0.0]
    avg = [0.0,0.0]
    for o in neighbors:
        avg = add(avg, o.vel)
    avg = div(avg, len(neighbors))
    return avg
