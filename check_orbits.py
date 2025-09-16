#!/usr/bin/env python3
import sys, json

USAGE = "usage: check_orbits.py <solutions_pX.txt> [--with-swap]"

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print(USAGE); raise SystemExit(2)

words = sorted({line.strip().upper() for line in open(sys.argv[1]) if line.strip()})
with_swap = (len(sys.argv) == 3 and sys.argv[2] == "--with-swap")

def rots(w):
    return [w[i:] + w[:i] for i in range(len(w))]

def dihedral_orbit(w):
    #rotations + the reflection of each rotation generate all D_n elements
    orb = set()
    for r in rots(w):
        #rotation
        orb.add(r)
        #reflection after that rotation
        orb.add(r[::-1])
    return orb
  
#global color swap tau
def swap_colors(w): 
    return w.translate(str.maketrans("BR", "RB"))

def orbit(w):
    if not with_swap:
        return dihedral_orbit(w)
    #include global swap
    return dihedral_orbit(w) | dihedral_orbit(swap_colors(w))

unseen = set(words)
reps, sizes = [], []

while unseen:
    w = min(unseen)
    o = orbit(w) & set(words)
    reps.append(min(o))
    sizes.append(len(o))
    unseen -= o

print(json.dumps({
    "num_words": len(words),
    "num_orbits": len(sizes),
    "orbit_sizes": sizes,
    "reps": reps,
    "with_swap": with_swap
}, indent=2))