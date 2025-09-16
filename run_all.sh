#!/usr/bin/env bash
set -euo pipefail

# Usage: ./run_all.sh [MAX_PRIME]
# Default MAX_PRIME is 997 if not provided.
MAXP="${1:-997}"

#prefer kissat for SAT speed if present; fall back to CaDiCaL.
SAT_SOLVER=""
if command -v kissat >/dev/null 2>&1; then
  SAT_SOLVER="kissat"
elif command -v cadical >/dev/null 2>&1; then
  SAT_SOLVER="cadical"
else
  echo "No SAT solver found (need kissat or cadical)"; exit 1
fi

#prefer CaDiCaL for UNSAT proof logging.
HAVE_CADICAL=0
command -v cadical >/dev/null 2>&1 && HAVE_CADICAL=1

HAVE_DRAT=0
command -v drat-trim >/dev/null 2>&1 && HAVE_DRAT=1

#generate primes 5..MAXP (simple sieve via Python).
PRIMES="$(python3 - "$MAXP" <<'PY'
import sys
MAX=int(sys.argv[1])
isp=[True]*(MAX+1)
if MAX>=0: isp[0]=False
if MAX>=1: isp[1]=False
import math
for i in range(2,int(math.isqrt(MAX))+1):
    if isp[i]:
        step=i
        start=i*i
        isp[start:MAX+1:step]=[False]*(((MAX-start)//step)+1)
print(" ".join(str(p) for p in range(5,MAX+1) if isp[p]))
PY
)"

SAT_P=()
UNSAT_P=()

for p in $PRIMES; do
  cnf=avoid_p${p}.cnf
  out=solver_p${p}.out
  echo "=== p=${p} ==="
  python3 make_cnf.py ${p} ${cnf}

  if (( p >= 13 )); then
    if (( HAVE_CADICAL )); then
      #solve with CaDiCaL and (attempt to) emit textual DRAT proof.
      #CaDiCaL syntax: cadical <cnf> <proof>
      cadical ${cnf} avoid_p${p}.drat > ${out} || true

      #check solver status from output.
      satline=$(grep -m1 -E '^s (SATISFIABLE|UNSATISFIABLE)' ${out} || true)
      if echo "$satline" | grep -q 'UNSAT'; then
        #verify DRAT if drat-trim is available.
        if (( HAVE_DRAT )); then
          if drat-trim ${cnf} avoid_p${p}.drat -q; then
            echo "DRAT verified for p=${p}"
            UNSAT_P+=("${p}")
          else
            echo "DRAT check FAILED for p=${p}"; exit 1
          fi
        else
          echo "drat-trim not found; skipped proof check for p=${p}"
          UNSAT_P+=("${p}")
        fi
      elif echo "$satline" | grep -q 'SATISFIABLE'; then
        echo "Unexpected SAT from CaDiCaL for p=${p}; extracting a model..."
        #get a model with the chosen SAT solver and verify it.
        ${SAT_SOLVER} -q ${cnf} > ${out}.sat || true
        satline2=$(grep -m1 -E '^s (SATISFIABLE|UNSATISFIABLE)' ${out}.sat || true)
        if echo "$satline2" | grep -q 'UNSAT'; then
          echo "WARNING: ${SAT_SOLVER} claims UNSAT too for p=${p}."
        else
          w=$(python3 model_to_word.py ${p} ${out}.sat)
          echo "witness p=${p}: ${w}"
          python3 verifier_strong_form.py ${p} "${w}"
          SAT_P+=("${p}")
        fi
      else
        echo "WARNING: could not parse solver status for p=${p} (see ${out})."
      fi
    else
      echo "WARNING: CaDiCaL not found; solving p=${p} without a proof."
      ${SAT_SOLVER} -q ${cnf} > ${out} || true
      satline=$(grep -m1 -E '^s (SATISFIABLE|UNSATISFIABLE)' ${out} || true)
      if echo "$satline" | grep -q 'SATISFIABLE'; then
        w=$(python3 model_to_word.py ${p} ${out})
        echo "witness p=${p}: ${w}"
        python3 verifier_strong_form.py ${p} "${w}"
        SAT_P+=("${p}")
      else
        echo "UNSAT (no proof logged) for p=${p}"
        UNSAT_P+=("${p}")
      fi
    fi

  else
    #p < 13: SAT branch — get model, decode, verify with the 42-check.
    if [[ "${SAT_SOLVER}" == "kissat" ]]; then
      kissat -q ${cnf} > ${out} || true
    else
      cadical ${cnf} > ${out} || true
    fi
    satline=$(grep -m1 -E '^s (SATISFIABLE|UNSATISFIABLE)' ${out} || true)
    if echo "$satline" | grep -q 'UNSAT'; then
      echo "Unexpected UNSAT for p=${p}. Check ${out}."
      continue
    fi
    w=$(python3 model_to_word.py ${p} ${out})
    echo "witness p=${p}: ${w}"
    python3 verifier_strong_form.py ${p} "${w}"
    SAT_P+=("${p}")
  fi
done

echo
echo "==== SUMMARY ===="
if ((${#SAT_P[@]})); then
  echo "SAT primes (witness found): ${SAT_P[*]}"
else
  echo "SAT primes (witness found): none"
fi

if ((${#UNSAT_P[@]})); then
  echo "UNSAT primes (DRAT verified or declared): ${UNSAT_P[*]}"
else
  echo "UNSAT primes (DRAT verified or declared): none"
fi