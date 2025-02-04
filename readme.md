# README.md

# Project: Optimized Davis–Putnam/DPLL SAT Solver

## Overview

This project contains several implementations of the Davis–Putnam and DPLL algorithms for solving SAT problems. The project includes:
- A **baseline DP implementation** (`dp_default.py`) that follows the classic approach.
- An **optimized DP variant** (`dp`) that uses improved data structures and heuristics.
- Two versions of the **DPLL algorithm**:
  - `classical_dpll`: A standard DPLL implementation without additional heuristics.
  - `dpll`: A heuristic-based DPLL.
  - `dpll_watchers`: A DPLL variant that implements the two-literal watching scheme for efficient unit propagation.

Performance measurements and profiling results have been collected on benchmark CNF files from the SATLIB suite.

## Repository Structure

```
.
├── dp_baseline.py         # Baseline DP implementation (dp_default)
├── dpll.py                # DPLL and classical_dpll implementations with optimizations and heuristics
├── dpll_watchers.py       # DPLL implementation with two-literal watchers
├── main.py                # Main entry point for running tests
├── utils.py               # Utility functions (CNF parsing, counters, etc.)
├── schedule_runs.sh       # Bash script to run the tests across different implementations
├── uf50/                 # SAT benchmark CNF files (satisfiable)
├── uuf50/                # UNSAT benchmark CNF files
├── uf175-01.cnf         # Large SAT instance
└── uuf150-01.cnf        # Large UNSAT instance
```

## Requirements

- Python 3.10+  
- [PyPy](https://www.pypy.org/) (optional but recommended for enhanced performance)
- Standard Python libraries (e.g., `argparse`, `logging`, `time`)

For generating graphs, you will also need:
- `pandas`
- `seaborn`
- `matplotlib`

Install these packages (if not already installed) via:
```bash
pip install pandas seaborn matplotlib
```

## How to Run

### Command-Line Arguments

Run the main script (`main.py`) with the following command-line options:

- `--algorithm`: Specify the algorithm to use. Choices include:
  - `dp_default`
  - `dp`
  - `classical_dpll`
  - `dpll`
  - `dpll_watchers`
- `--num_runs`: The number of runs per CNF file (default is 1).
- `--run_on_large_cnf`: Set to `True` to include large CNF files in the test.
- `--run_on_large_cnf_only`: Set to `True` to run tests only on large CNF files.
- `--log_level`: Set the logging level (e.g., `DEBUG`, `INFO`).

### Example Usage

Run the heuristic-based DPLL with watchers on all small CNF files for 10 runs each:
```bash
python3 main.py --algorithm dpll_watchers --num_runs 10
```

Run the optimized DP algorithm on large problems only (using PyPy for best performance):
```bash
pypy/bin/pypy main.py --algorithm dp --num_runs 1 --run_on_large_cnf_only True
```

### Using the Bash Script

A shell script (`schedule_runs.sh`) is provided to automate running multiple experiments. Make sure the script is executable:
```bash
chmod +x schedule_runs.sh
```
Then execute:
```bash
./schedule_runs.sh
```
This script will run tests on all algorithms under both CPython and PyPy, and for both small and large CNF instances (where feasible).

## Profiling and Graphs

Profiling was performed using `cProfile` and the results are saved in the `results/` directory. To generate comparative graphs, use the provided Python snippet (see the **Graphical Analysis** section in the report).

## Summary of Optimizations

- **Data Structures:** The use of `frozenset` for clauses and array-based literal frequency counts led to significant speed-ups.
- **Heuristics:** Improved branch selection through best literal selection reduced the number of recursive calls.
- **Two-Literal Watching:** This mechanism in the `dpll_watchers` implementation reduced the overhead during unit propagation.
- **PyPy Usage:** Running the algorithms under PyPy greatly improved performance, especially for recursive and data-structure–intensive methods.

For detailed performance metrics and discussions, please refer to `report.md`.

---

*For any questions or further details, please contact [malchemis@proton.me].*