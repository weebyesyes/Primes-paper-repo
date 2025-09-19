# Artifacts and scripts

- `verifier_strong_form.py`: residue-window checker
- `make_cnf.py`: CNF generator
- `model_to_word.py`: decode SAT model to word
- `check_orbits.py`: orbit summary under dihedral action
- `run_all.sh`: convenience runner
- `solutions_p5.txt`, `solutions_p7.txt`, `solutions_p11.txt`: complete solution lists
- `find_wc42.py` — composite-modulus sweep for the cyclic vdW number at `(k,r)=(4,2)` (non-degenerate windows only)
- `verifier_cyclic.py` — verifier for composite moduli (checks only **non-degenerate** residue windows)

## Examples
```bash
python3 verifier_strong_form.py 7 BBBRBRR
python3 make_cnf.py 13 avoid_p13.cnf
kissat --proof=avoid_p13.drat --no-binary avoid_p13.cnf > solver_p13.log
drat-trim avoid_p13.cnf avoid_p13.drat -q
python3 check_orbits.py solutions_p7.txt
```
