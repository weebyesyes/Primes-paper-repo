#!/usr/bin/env python3
"""
Requires: cadical (preferred) or kissat, drat-trim preferred.
"""

import argparse, os, shutil, subprocess, sys
from typing import List, Tuple

#filesystem helpers

def ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)

def write_text(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def append_text(path: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)

#system helpers

def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run(cmd: List[str], *, input_text: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True, check=False)

def solver_status(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("s "):
            if "UNSATISFIABLE" in line: return "UNSAT"
            if "SATISFIABLE" in line:   return "SAT"
    return "UNKNOWN"

#combinatorics

def nondeg_windows(M: int):
    for r in range(1, M):
        for i in range(M):
            w=[(i+k*r)%M for k in range(4)]
            if len(set(w))==4:
                yield tuple(w)

def is_valid_witness(word: str) -> bool:
    M = len(word)
    for a,b,c,d in nondeg_windows(M):
        block = [word[a], word[b], word[c], word[d]]
        if block.count('B')==4 or block.count('R')==4:
            return False
    return True

def build_dimacs_for_M(M: int) -> str:
    clauses=[]
    def var(i: int) -> int: return i+1
    for a,b,c,d in nondeg_windows(M):
        vs=[var(a),var(b),var(c),var(d)]
        clauses.append(vs)               # forbid BBBB
        clauses.append([-v for v in vs]) # forbid RRRR
    lines=[f"p cnf {M} {len(clauses)}"]
    for C in clauses: lines.append(" ".join(map(str,C))+" 0")
    return "\n".join(lines)+"\n"

def decode_model_strict(stdout: str, M: int) -> str | None:
    """Parse only 'v ' lines; return word over {B,R} or None if not found."""
    vals = {}
    saw = False
    model_lines=[]
    for line in stdout.splitlines():
        if line.startswith("v "):
            saw = True
            model_lines.append(line+"\n")
            for tok in line.split()[1:]:
                if tok == '0': continue
                if tok.lstrip('-').isdigit():
                    v=int(tok); vals[abs(v)] = (v>0)
    if not saw: return None
    word = "".join('R' if vals.get(i,False) else 'B' for i in range(1, M+1))
    return word

#solve one modulus

def solve_one(M: int, outdir: str, prefer_kissat: bool) -> Tuple[str, str, str]:
    """
    Returns (status, witness_or_note, proof_note)
    and writes artifacts into outdir.
    """
    ensure_dir(outdir)
    cnf_path   = os.path.join(outdir, f"avoid_M{M}.cnf")
    drat_path  = os.path.join(outdir, f"proof_M{M}.drat")
    check_path = os.path.join(outdir, f"proof_M{M}.drat.check.txt")
    model_path = os.path.join(outdir, f"model_M{M}.txt")
    wit_path   = os.path.join(outdir, f"witness_M{M}.txt")

    write_text(cnf_path, build_dimacs_for_M(M))

    have_cad   = have("cadical")
    have_kisat = have("kissat")
    have_drat  = have("drat-trim")

    use_cad = (have_cad and not prefer_kissat) or (have_cad and not have_kisat)

    if use_cad:
        proc = run(["cadical", cnf_path, drat_path])
        st = solver_status(proc.stdout)
        if st == "SAT":
            #save full stdout for provenance (includes v-lines)
            write_text(model_path, proc.stdout)
            word = decode_model_strict(proc.stdout, M)
            #fallback to kissat for clean model if needed
            if (word is None or not is_valid_witness(word)) and have_kisat:
                k = run(["kissat", "-q", cnf_path])
                if solver_status(k.stdout) == "SAT":
                    append_text(model_path, "\n# kissat stdout\n"+k.stdout)
                    w2 = decode_model_strict(k.stdout, M)
                    if w2 is not None: word = w2
            if word is None:
                return "SAT", "no model parsed", ""
            write_text(wit_path, word+"\n")
            note = ""
            if not is_valid_witness(word):
                note = "witness FAILS self-check"
            return "SAT", word if not note else f"{word}\t{note}", ""
        elif st == "UNSAT":
            proofnote = "no drat-trim"
            if have_drat:
                chk = run(["drat-trim", cnf_path, drat_path, "-q"])
                write_text(check_path, chk.stdout + chk.stderr)
                if ("s VERIFIED" in chk.stdout) or (chk.returncode == 0):
                    proofnote = "DRAT ok"
                else:
                    proofnote = "DRAT check failed"
            return "UNSAT", "", proofnote
        else:
            return "UNKNOWN", "", ""
    else:
        if not have_kisat:
            return "UNKNOWN", "", "no solver found"
        proc = run(["kissat", "-q", cnf_path])
        st = solver_status(proc.stdout)
        if st == "SAT":
            write_text(model_path, proc.stdout)
            word = decode_model_strict(proc.stdout, M)
            if word is None:
                return "SAT", "no model parsed", ""
            write_text(wit_path, word+"\n")
            note = ""
            if not is_valid_witness(word):
                note = "witness FAILS self-check"
            return "SAT", word if not note else f"{word}\t{note}", ""
        elif st == "UNSAT":
            return "UNSAT", "", ""  # no DRAT
        else:
            return "UNKNOWN", "", ""

#CLI

def main():
    ap = argparse.ArgumentParser(description="Sweep M to help determine W_c(4,2) with file outputs.")
    ap.add_argument("--start", type=int, default=13)
    ap.add_argument("--end", type=int, default=34)
    ap.add_argument("--outdir", type=str, default="results")
    ap.add_argument("--csv", type=str, default="wc42_results.csv")
    ap.add_argument("--tsv", type=str, default="wc42_results.tsv")
    ap.add_argument("--prefer-kissat", action="store_true",
                    help="Prefer Kissat even if CaDiCaL is available (no DRAT).")
    args = ap.parse_args()

    ensure_dir(args.outdir)
    csv_path = os.path.join(args.outdir, args.csv) if args.csv else ""
    tsv_path = os.path.join(args.outdir, args.tsv) if args.tsv else ""

    rows = []
    print("M\tStatus\tWitness/Note\tProof")
    for M in range(args.start, args.end + 1):
        st, w, pr = solve_one(M, args.outdir, args.prefer_kissat)
        print(f"{M}\t{st}\t{w}\t{pr}")
        rows.append((M, st, w, pr))

    if csv_path:
        write_text(csv_path, "M,Status,Witness,Proof\n")
        for M, st, w, pr in rows:
            wq  = f"\"{w}\""  if ("," in w)  else w
            prq = f"\"{pr}\"" if ("," in pr) else pr
            append_text(csv_path, f"{M},{st},{wq},{prq}\n")
        print(f"[wrote] {csv_path}")

    if tsv_path:
        write_text(tsv_path, "M\tStatus\tWitness\tProof\n")
        for M, st, w, pr in rows:
            append_text(tsv_path, f"{M}\t{st}\t{w}\t{pr}\n")
        print(f"[wrote] {tsv_path}")

    #friendly summary
    sat_33 = any(M == 33 and st == "SAT" for (M, st, _, _) in rows)
    unsat_34 = any(M == 34 and st.startswith("UNSAT") for (M, st, _, _) in rows)
    if sat_33 and unsat_34:
        print("\nSummary: SAT at M=33 and UNSAT at M=34 -> W_c(4,2)=34.\n")

if __name__ == "__main__":
    main()