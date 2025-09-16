# Artifacts and scripts

- `verifier_strong_form.py`: residue-window checker
- `make_cnf.py`: CNF generator
- `model_to_word.py`: decode SAT model to word
- `check_orbits.py`: orbit summary under dihedral action
- `run_all.sh`: convenience runner
- `solutions_p5.txt`, `solutions_p7.txt`, `solutions_p11.txt`: complete solution lists

## Examples
```bash
python3 verifier_strong_form.py 7 BBBRBRR
python3 make_cnf.py 13 avoid_p13.cnf
kissat --proof=avoid_p13.drat --no-binary avoid_p13.cnf > solver_p13.log
drat-trim avoid_p13.cnf avoid_p13.drat -q
python3 check_orbits.py solutions_p7.txt
```
