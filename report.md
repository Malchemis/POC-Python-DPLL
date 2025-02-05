# Optimizing the Davis–Putnam Algorithm: A Comprehensive Analysis

*Date: 2025-02-04*  
*Author: Elias BOULANGER*

Note: The time and profiling results were obtained by running the code on
a machine with the following specifications:
- Processor: AMD Ryzen™ 5 3550H with Radeon™ Vega Mobile Gfx × 8
- RAM: 24 GB
- OS: Ubuntu 24.04.1 LTS
- Python Version: 3.12.0
- PyPy Version: PyPy3.10 at [https://pypy.org/download.html](https://pypy.org/download.html)
- SATLIB Benchmark Files: uf50, uuf50, uf175-01, uuf150-01

---

## Abstract

In this project, we have revisited the classical Davis–Putnam (DP) algorithm for 
solving Boolean satisfiability (SAT) and explored a series of optimizations to 
improve its performance. Our approach entailed refactoring the baseline implementation
to use more efficient data structures (e.g., immutable sets for clauses, array-based 
indexing) and implementing advanced techniques such as heuristic branching and the 
two-literal watching scheme. We developed several variants—namely, the baseline 
`dp_default`, an optimized DP with heuristics `dp`, a classical DPLL implementation 
`classical_dpll`, a heuristic-based DPLL `dpll`, and a further enhanced version 
with literal watchers `dpll_watchers`. Performance tests on SATLIB benchmark files 
and profiling results guided our optimizations. In addition, we investigated the 
impact of running these algorithms under Pure Python versus PyPy, with the latter 
yielding significant speed improvements for some implementations. This report details
our methodology, presents timing and profiling results, and discusses the observed 
performance gains.

---

## 1. Introduction

Boolean satisfiability (SAT) is a fundamental problem in theoretical computer 
science with many practical applications. The Davis–Putnam algorithm, and its
subsequent DPLL (Davis–Putnam–Logemann–Loveland) refinement, form the basis 
for many modern SAT solvers. However, the efficiency of these algorithms depends 
crucially on the order in which clauses are processed, the data structures used,
and the heuristics employed for variable selection and unit propagation.

Our project set out to optimize a provided baseline DP implementation (`dp_default.py`)
by addressing several performance bottlenecks:
- Replacing Python lists with immutable data structures (e.g., `frozenset`) to 
leverage efficient set operations.
- Minimizing redundant computations (e.g., computing tautologies only once).
- Using array-based indexing for direct literal lookup.
- Integrating heuristic methods such as pure literal elimination and best literal 
selection.
- Implementing the two-literal watching scheme in our `dpll_watchers` variant to 
reduce the overhead in unit propagation.

In addition, we compared our improvements against both Pure Python and PyPy to
assess the benefits of alternative Python interpreters.

---

## 2. Methods

### 2.1 Baseline Implementation Analysis

The original `dp_default` code applied a series of transformation rules 
(removal of tautologies, unit clause propagation, pure literal elimination, 
and superset clause removal) recursively. Our profiling of `dp_default` 
(using a representative run on SATLIB files repeated 10 times) showed that:

- **Function Call Overhead:** Over 2.3 billion function calls were made with a 
cumulative time of over 257 seconds.  
- **High-Frequency Operations:** Functions such as `formulas_equal`, `third_rule`,
and `find_single_literal` (which internally calls `exists_in_clauses`) dominated 
the runtime. For example, `exists_in_clauses` was called over 67 million times, 
suggesting that frequent membership tests on lists were a major bottleneck.
- **Data Structure Limitations:** The use of Python lists and repeated iteration 
through clauses led to significant overhead.

### 2.2 Optimization Strategies

Based on the profiling insights, we introduced several key modifications:

#### 2.2.1 Data Structure Enhancements

- **Immutable Sets for Clauses:** Converting clauses to `frozenset` objects 
allowed for fast membership tests.
- **Array-Based Lookups:** In the DPLL variants, we replaced iterative searches 
with fixed-size arrays (or lists indexed by variable number) to quickly compute 
literal frequencies and branch selection scores. A first implementation used dictionaries
but was later optimized to use arrays for better performance (dictionaries were around
2-4 times slower due to the overhead of hashing).

#### 2.2.2 Heuristic Improvements

- **Best Literal Selection:** In the optimized `dp` and `dpll` implementations, 
we computed a score for each literal based on its frequency (using separate 
arrays for positive and negative occurrences). This heuristic reduced the search 
space by choosing the literal with the highest combined frequency. One other improvement we
have observed is that you once you have found the best literal, you can compare the frequency
of both polarities and return the one with the highest frequency.
- **Pure Literal and Unit Propagation:** Our refined implementations repeatedly 
applied unit propagation and pure literal elimination, taking advantage of set 
comprehensions and early termination when the clause set was empty or contained 
an empty clause.
  Rule4 (subsumption) has been determined to not be useful in our case 
as it was not activated a lot, and took a lot of time to compute.

#### 2.2.3 Two-Literal Watching

- **Watcher Data Structure:** The `dpll_watchers` implementation employs the 
two-literal watching scheme to monitor each clause with at most two “watched” 
literals. When an assignment is made, only the clauses watching the negated 
literal are examined, significantly reducing the number of operations during 
unit propagation. As we only need to detect when a clause becomes unit (or empty),
we can skip clauses that are already satisfied or contain the assigned literal.
- **State Restoration:** For branching, the algorithm saves the state of the 
formula (active clauses, frequency arrays, occurrence lists, and watchers) to 
allow backtracking without recomputation. This part is quite heavy on the memory
and it could be improved with incremental undo mechanisms.

#### 2.2.4 Interpreter Considerations

- **PyPy vs. Pure Python:** Benchmarking showed that certain methods 
(especially those using heavy recursion and dynamic memory allocation) 
benefited significantly from PyPy’s JIT compilation. For example, the 
watcher-based DPLL (`dpll_watchers`) ran in approximately 5–7 seconds 
on large problems under PyPy, compared to roughly 24–30 seconds using Pure Python.

---

## 3. Results

### 3.1 Execution Time Comparisons

Our experiments ran multiple algorithms on both SAT and UNSAT instances from the SATLIB benchmark suites. For each algorithm, we recorded:
- Total run time
- Average run time per file
- Number of recursive calls (or “algorithm calls”)

Below is a summary (extracted from our logs). 
The time is given in seconds unless expressed otherwise,
the recursive calls are calls per file given as a range (min–max) across all files.

| Algorithm                         | uf50/*     | uuf50/*    | Large Instance (uf175-uuf150) | Min-Max Recursive Calls (on small across all files) | Large Instance Recursive Calls (uf175-uuf150) |
|-----------------------------------|------------|------------|-------------------------------|-----------------------------------------------------|-----------------------------------------------|
| **dp_default**                    | 0.05–1     | 0.8–2.15   | (too long to run >> 2H)       | 31–4109                                             | N/A                                           |
| **dp (optimized)**                | 0.003–0.04 | 0.23–0.55  | 34 - 54                       | 14–250                                              | 22715 – 42239                                 |
| **classical_dpll (no heuristic)** | 0.001–0.04 | 0.03–0.08  | (too long to run >> 2H)       | 13–609                                              | N/A                                           |
| **dpll (heuristic)**              | 0.002–0.02 | 0.01–0.03  | 24 - 29                       | 22–178                                              | 19155 – 27501                                 |
| **dpll_watchers**                 | 0.002–0.02 | 0.007–0.02 | 6 - 7                         | 14–87                                               | 7936 - 11398                                  |

*Note:* The times above are averages across multiple runs (10 runs per file) 
and reflect PyPy execution, which provided the most consistent speed-ups.

To see all the results in detail, refer to the detailed logs in the `results/` 
directory.

### 3.2 Profiling Insights

#### Baseline (`dp_default`)

- **Cumulative Time:** Over 257 seconds.
- **Bottleneck Functions:** 
  - `exists_in_clauses` and `find_single_literal` (together consuming ~80 seconds 
cumulatively).
  - List comprehensions in `remove_value_from_clauses` and `remove_clauses_with_value`.

#### Optimized DPLL (`dpll`)

- **Cumulative Time:** Roughly 3.87 seconds.
- **Key Improvements:** Direct array indexing and set operations significantly 
reduced the time spent on clause manipulations. Heuristic branching also helped a lot 
on large instances.
- **Bottleneck Functions:**
  - The method `add` of sets (due to the frequent clause updates).
  - The heuristic unit propagation and best literal search, but these operations 
were far less expensive due to array-based counting and set operations.
  
#### DPLL with Watchers (`dpll_watchers`)

- **Cumulative Time:** Approximately 3.07 seconds overall (with significantly 
fewer recursive calls).
- **Key Improvements:** The two-literal watching mechanism limited the need to
iterate over all clauses, thereby reducing the cumulative cost of unit propagation.
  We detect early when we need to propagate a unit clause, and we only need to check the clauses that 
are watching the negated literal.
- **Bottleneck Functions:**:
  - State Restoration: The memory overhead of saving the state for backtracking
was noticeable but necessary for efficient branching.
  - `has_empty_clause` is called frequently, can be optimized further by taking advantage
of the 2-literal watching scheme.

## 4. Discussion

The results confirm that careful algorithmic optimizations and the appropriate 
data structure and heuristic choices can dramatically improve performance:

- **Data Structures:** Replacing list-based operations with set operations 
(using `frozenset`) and array indexing led to orders-of-magnitude speed-ups.
For example, the optimized `dp` algorithm runs almost 20–30 times faster than 
the baseline.
- **Heuristic Branching:** By using literal frequency counts for branch selection, 
the search space is pruned more effectively, reducing the number of recursive calls.
- **Two-Literal Watching:** The implementation in `dpll_watchers` reduced the 
cost of unit propagation by focusing only on the clauses that may become unit, 
rather than iterating over all clauses.
- **Interpreter Choice:** PyPy’s JIT compilation dramatically reduced the 
runtime—especially for the algorithms that rely on recursion and dynamic data 
structure manipulations—underscoring the importance of choosing the right 
interpreter for performance-critical applications.

In conclusion, the combination of these optimizations not only reduced the 
cumulative number of function calls but also reduced the per-call cost, 
leading to significant overall runtime improvements.

---

## 5. Conclusion

This project demonstrates that both algorithmic strategies and 
low-level implementation details (such as data structures and interpreter choice)
are critical in optimizing SAT solvers. Our experimental results, supported by 
detailed profiling, indicate that the optimized DP and DPLL algorithms 
(especially those using heuristics and the two-literal watching scheme) 
significantly outperform the baseline implementation. Furthermore, the dramatic
improvements observed with PyPy highlight an often-underappreciated aspect of 
performance engineering in Python. Future work could explore incremental undo 
mechanisms for state restoration and further refinements in branching heuristics.

---

# References

1. Wikipédia DPLL: https://en.wikipedia.org/wiki/DPLL_algorithm
2. Wikipédia DP: https://en.wikipedia.org/wiki/Davis%E2%80%93Putnam_algorithm
3. Blog Post 2-Literal Watching: http://haz-tech.blogspot.com/2010/08/whos-watching-watch-literals.html?m=1
4. SATLIB Benchmark Suite: [http://www.cs.ubc.ca/~hoos/SATLIB/benchm.html](http://www.cs.ubc.ca/~hoos/SATLIB/benchm.html)

---