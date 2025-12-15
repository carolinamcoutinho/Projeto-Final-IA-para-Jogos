import math

def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def normalize(v):
    mag = math.hypot(v[0], v[1])
    if mag == 0:
        return [0,0]
    return [v[0]/mag, v[1]/mag]

def add(a, b):
    return [a[0]+b[0], a[1]+b[1]]

def sub(a, b):
    return [a[0]-b[0], a[1]-b[1]]

def mul(a, s):
    return [a[0]*s, a[1]*s]

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1]

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x
