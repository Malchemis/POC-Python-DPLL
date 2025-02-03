import time
from typing import List, Set, Callable, FrozenSet

# Type aliases for clarity
Literal = int
Clause = FrozenSet[Literal]
CNF = Set[Clause]


class Counter:
    """
    A simple counter-class to keep track of the number of times a function is called.
    """
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

    def __iadd__(self, other):
        self.count += other
        return self


class ChangeTracker:
    """
    A wrapper around a boolean variable to keep track of changes.
    """
    def __init__(self):
        self.changed = False

    def set_changed(self):
        self.changed = True

    def reset_changed(self):
        self.changed = False

    def __bool__(self):
        return self.changed


def read_cnf(file_path: str) -> (CNF, int):
    """
    Read a CNF file in DIMACS format and return a set of clauses.

    :param file_path: Path to the CNF file.
    :return: A set of frozensets, where each inner frozenset represents a clause.
    """
    clauses: Set[Clause] = set()
    n_vars = 0
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('%'):
                break
            if line.startswith('c'):
                continue
            if line.startswith('p'):
                n_vars = int(line.strip().split()[2])
                continue
            literals = list(map(int, line.strip().split()))
            if literals and literals[-1] == 0:
                literals.pop()
            if literals:
                clauses.add(frozenset(literals))
    return set(clauses), n_vars


def run_dp_on_files(cnf_files: List[str], algorithm: Callable, logger=None) -> float:
    """
    Run the DP algorithm on a list of CNF files.

    :param algorithm: The algorithm to use (default is dp). Must return a tuple (bool, int).
    :param cnf_files: List of file paths to CNF files.
    :param logger: The logger object to use for logging.
    :return: The total time taken to run the algorithm on all files.
    """
    sum_times = 0.0
    n_vars = 0
    for cnf_file in cnf_files:
        counter = Counter()
        file_clauses = None
        try:
            file_clauses, n_vars = read_cnf(cnf_file)
        except FileNotFoundError:
            logger.error(f'File not found: {cnf_file}')

        logger.info(f'Starting DP with clauses from {cnf_file}')
        start_time = time.time()
        satisfiable = algorithm(file_clauses, counter=counter, logger=logger, n_vars=n_vars)
        end_time = time.time()
        logger.info(
            f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} '
            f'in {end_time - start_time:.5f} seconds.'
            f' {algorithm.__name__} called {counter.count} times.'
        )
        sum_times += end_time - start_time
    return sum_times