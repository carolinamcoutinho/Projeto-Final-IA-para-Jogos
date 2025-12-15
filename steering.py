from utils import normalize, sub, mul

def seek(pos, target, speed):
    d = normalize(sub(target, pos))
    return [d[0]*speed, d[1]*speed]

def flee(pos, target, speed):
    d = normalize(sub(pos, target))
    return [d[0]*speed, d[1]*speed]

def separation(npc, neighbors):
    force = [0,0]
    for other in neighbors:
        diff = sub(npc.pos, other.pos)
        dist = (diff[0]**2 + diff[1]**2)**0.5
        if dist < 50:
            d = normalize(diff)
            force[0] += d[0]*(60/dist)
            force[1] += d[1]*(60/dist)
    return force

def cohesion(npc, neighbors):
    if not neighbors:
        return [0,0]
    avg = [0,0]
    for n in neighbors:
        avg[0] += n.pos[0]
        avg[1] += n.pos[1]
    avg = [avg[0]/len(neighbors), avg[1]/len(neighbors)]
    return seek(npc.pos, avg, 40)

def alignment(npc, neighbors):
    if not neighbors:
        return [0,0]
    avg = [0,0]
    for n in neighbors:
        avg[0] += n.vel[0]
        avg[1] += n.vel[1]
    avg = [avg[0]/len(neighbors), avg[1]/len(neighbors)]
    return avg
