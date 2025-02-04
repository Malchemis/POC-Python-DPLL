#!/bin/bash

# This script is used to schedule the runs of the script

# First we run 10 times every algorithm with pure python on small problems
echo "Running via Python algorithm dp_default 10 times..."
python3 main.py --algorithm dp_default --num_runs 10      # Baseline DP
echo "Running via Python algorithm dp 10 times..."
python3 main.py --algorithm dp --num_runs 10              # DP optimized and with Heuristics
echo "Running via Python algorithm classical_dpll 10 times..."
python3 main.py --algorithm classical_dpll --num_runs 10  # DPLL with no heuristics
echo "Running via Python algorithm dpll 10 times..."
python3 main.py --algorithm dpll --num_runs 10            # DPLL with heuristics
echo "Running via Python algorithm dpll_watchers 10 times..."
python3 main.py --algorithm dpll_watchers --num_runs 10   # DPLL with watchers and optimized structure

# Then we run 10 times every algorithm with PyPy on small problems
echo "Running via PyPy algorithm dp_default 10 times..."
pypy/bin/pypy main.py --algorithm dp_default --num_runs 10
echo "Running via PyPy algorithm dp 10 times..."
pypy/bin/pypy main.py --algorithm dp --num_runs 10
echo "Running via PyPy algorithm classical_dpll 10 times..."
pypy/bin/pypy main.py --algorithm classical_dpll --num_runs 10
echo "Running via PyPy algorithm dpll 10 times..."
pypy/bin/pypy main.py --algorithm dpll --num_runs 10
echo "Running via PyPy algorithm dpll_watchers 10 times..."
pypy/bin/pypy main.py --algorithm dpll_watchers --num_runs 10

# Then we run one time the big problems only on all algorithms with PyPy
# echo "Running via PyPy algorithm dp_default 1 time on large problems only..."
# We actually don't run the baseline (more than 1H with no result for both problems)
# pypy/bin/pypy main.py --algorithm dp_default --num_runs 1 --run_on_large_cnf_only True

echo "Running via PyPy algorithm dp 1 time on large problems only..."
pypy/bin/pypy main.py --algorithm dp --num_runs 1 --run_on_large_cnf_only True
#also too slow (more than 2h with no results)
#echo "Running via PyPy algorithm classical_dpll 1 time on large problems only..."
#pypy/bin/pypy main.py --algorithm classical_dpll --num_runs 1 --run_on_large_cnf_only True
echo "Running via PyPy algorithm dpll 1 time on large problems only..."
pypy/bin/pypy main.py --algorithm dpll --num_runs 1 --run_on_large_cnf_only True
echo "Running via PyPy algorithm dpll_watchers 1 time on large problems only..."
pypy/bin/pypy main.py --algorithm dpll_watchers --num_runs 1 --run_on_large_cnf_only True