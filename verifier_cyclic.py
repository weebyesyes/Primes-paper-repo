#!/usr/bin/env python3
import sys

USAGE = "usage: verifier_cyclic.py <modulus M> <wordoverBR>"

def nondeg_windows(M):
    for r in range(1, M):
        for i in range(M):
            w=[(i+k*r)%M for k in range(4)]
            if len(set(w))==4:
                yield w

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(USAGE); sys.exit(2)
    M = int(sys.argv[1])
    w = sys.argv[2].strip().upper()
    assert len(w)==M and set(w)<=set("BR")
    for a,b,c,d in nondeg_windows(M):
        block=[w[a],w[b],w[c],w[d]]
        if block.count('B')==4 or block.count('R')==4:
            print("FAIL at", (a,b,c,d), "block=", "".join(block))
            sys.exit(1)
    print("OK")
