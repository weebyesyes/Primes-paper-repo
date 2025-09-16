#!/usr/bin/env python3
import sys
if len(sys.argv)!=3:
  print("usage: make_cnf.py <prime p> <out.cnf>"); 
  raise SystemExit(2)

p=int(sys.argv[1]); 
out=sys.argv[2]

def idx(i): 
  return i+1

def windows(p):
  for r in range(1,p):
    for i in range(p):
      yield [(i+k*r)%p for k in range(4)]
      
clauses=[]
for win in windows(p):
  vs=[idx(j) for j in win]
  clauses.append(vs)
  clauses.append([-v for v in vs])
with open(out,'w') as f:
  f.write(f"p cnf {p} {len(clauses)}\n")
  for C in clauses: 
    f.write(" ".join(map(str,C))+" 0\n")
