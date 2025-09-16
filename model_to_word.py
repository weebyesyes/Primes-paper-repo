#!/usr/bin/env python3
import sys, re

if len(sys.argv) != 3:
    print("usage: model_to_word.py <p> <solver_output>")
    raise SystemExit(2)

p = int(sys.argv[1])
path = sys.argv[2]

vals = {}  #var index -> boolean
for line in open(path, 'r', encoding='utf-8', errors='ignore'):
    #accept typical SAT outputs: lines may start with 'v', 's', etc.
    for tok in line.split():
        if re.fullmatch(r"-?\d+", tok):
            v = int(tok)
            if v == 0:
                continue
            vals[abs(v)] = (v > 0)

#default any missing variable to False (= 'B') to be safe
word = "".join('R' if vals.get(i, False) else 'B' for i in range(1, p+1))
print(word)
