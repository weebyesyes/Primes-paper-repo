#!/usr/bin/env python3
import sys
if len(sys.argv) != 3:
    print("usage: verifier_strong_form.py <prime p> <word>"); 
    raise SystemExit(2)

p = int(sys.argv[1]); 
w = sys.argv[2].strip().upper()
assert p >= 2 and len(w) == p and set(w)<=set("BR")

for r in range(1,p):
  for i in range(p):
    win=[w[(i+k*r)%p] for k in range(4)]
    if win.count('B')==4 or win.count('R')==4: 
      print("FAIL"); raise SystemExit(1)
  
print("OK")