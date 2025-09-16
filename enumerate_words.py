#!/usr/bin/env python3
# enumerate_words.py
# Enumerate all valid words for modulus p and compute D_p & D_p x <tau> orbit summaries.

from itertools import product
import sys, json

def residues_4ap_indices(p):
    for r in range(1, p):
        for i in range(p):
            yield (i%p, (i+r)%p, (i+2*r)%p, (i+3*r)%p)

def is_valid_word(word, p):
    bits = [1 if ch=='R' else 0 for ch in word]
    for a,b,c,d in residues_4ap_indices(p):
        s = bits[a] + bits[b] + bits[c] + bits[d]
        if s==0 or s==4:
            return False
    return True

def rot(word, k):
    p = len(word)
    return ''.join(word[(i-k)%p] for i in range(p))

def refl(word, k):
    p = len(word)
    return ''.join(word[(k - i) % p] for i in range(p))

def dihedral_orbit(word):
    p = len(word)
    seen = set()
    for k in range(p):
        seen.add(rot(word, k))
        seen.add(refl(word, k))
    return seen

def orbit_representatives(words):
    remaining = set(words)
    orbits, reps = [], []
    while remaining:
        w = min(remaining)
        orb = dihedral_orbit(w)
        orbits.append(orb)
        reps.append(w)
        remaining -= orb
    return orbits, reps

def main():
    if len(sys.argv)!=2:
        print("Usage: python enumerate_words.py <prime p>")
        sys.exit(2)
    p = int(sys.argv[1])
    #enumerate
    valid = []
    for tup in product('BR', repeat=p):
        w = ''.join(tup)
        if is_valid_word(w, p):
            valid.append(w)
    #write list
    with open(f"solutions_p{p}.txt","w") as f:
        for w in valid:
            f.write(w+"\n")
    #orbit summary
    orbits, reps = orbit_representatives(valid)
    d_orbits = [{'size': len(orb), 'rep': min(orb)} for orb in orbits]
    #group under global swap
    swap = lambda w: ''.join('R' if ch=='B' else 'B' for ch in w)
    rep_to_idx = {o['rep']: idx for idx, o in enumerate(d_orbits)}
    used = set()
    dp_tau = []
    for idx, o in enumerate(d_orbits):
        if idx in used: 
            continue
        rep = o['rep']
        swap_rep = min(dihedral_orbit(swap(rep)))
        j = rep_to_idx.get(swap_rep, None)
        if j is None or j==idx:
            group = {'reps': [rep], 'total_size': o['size']}
            used.add(idx)
        else:
            group = {'reps': sorted([rep, d_orbits[j]['rep']]), 
                     'total_size': o['size'] + d_orbits[j]['size']}
            used.add(idx); used.add(j)
        dp_tau.append(group)
    summary = {
        'p': p,
        'num_valid': len(valid),
        'Dp_orbits': d_orbits,
        'Dp_x_tau_orbits': dp_tau
    }
    with open(f"orbit_summary_p{p}.json","w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
