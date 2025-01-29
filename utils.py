import time
from typing import List, Set, Callable, FrozenSet

#Type aliases for clarity
Literal = int
Clause = FrozenSet[Literal]
CNF = Set[Clause]


def read_cnf(file_path: str) -> CNF:
    """
    Read a CNF file in DIMACS format and return a set of clauses.

    :param file_path: Path to the CNF file.
    :return: A set of frozensets, where each inner frozenset represents a clause.
    """
    clauses: Set[Clause] = set()
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('%'):
                break
            if line.startswith('c') or line.startswith('p'):
                continue
            literals = list(map(int, line.strip().split()))
            if literals and literals[-1] == 0:
                literals.pop()
            if literals:
                clauses.add(frozenset(literals))
    return set(clauses)


def run_dp_on_files(cnf_files: List[str], algorithm: Callable, logger=None) -> float:
    """
    Run the DP algorithm on a list of CNF files.

    :param algorithm: The algorithm to use (default is dp). Must return a tuple (bool, int).
    :param cnf_files: List of file paths to CNF files.
    :param logger: The logger object to use for logging.
    """
    sum_times = 0.0
    for cnf_file in cnf_files:
        counter = [0]
        file_clauses = None
        try:
            file_clauses = read_cnf(cnf_file)
        except FileNotFoundError:
            logger.error(f'File not found: {cnf_file}')

        logger.info(f'Starting DP with clauses from {cnf_file}')
        start_time = time.time()
        satisfiable = algorithm(file_clauses, counter=counter, logger=logger)
        end_time = time.time()
        logger.info(
            f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} '
            f'in {end_time - start_time:.3f} seconds.'
            f' DP called {counter[0]} times.'
        )
        sum_times += end_time - start_time
    return sum_times