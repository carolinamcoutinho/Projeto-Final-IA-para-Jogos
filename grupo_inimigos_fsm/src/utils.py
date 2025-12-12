# utils.py
import math

def vec(x=0, y=0):
    return [float(x), float(y)]

def add(a,b): return [a[0]+b[0], a[1]+b[1]]
def sub(a,b): return [a[0]-b[0], a[1]-b[1]]
def mul(v,s): return [v[0]*s, v[1]*s]
def div(v,s): return [v[0]/s, v[1]/s] if s!=0 else [0,0]
def length(v): return math.hypot(v[0], v[1])
def normalize(v):
    L = length(v)
    if L == 0: return [0.0, 0.0]
    return [v[0]/L, v[1]/L]
def distance(a,b):
    return length(sub(a,b))
