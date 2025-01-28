from typing import List, Set, Callable, FrozenSet
import time

#Type aliases for clarity
Literal = int
Clause = FrozenSet[Literal]
CNF = Set[Clause]

# Use any and list comprehension to check if a clause is a tautology
def is_tautology(clause: Clause) -> bool:
    """
    Check if a clause is a tautology (contains a literal and its negation).

    :param clause: A frozenset representing a clause.
    :return: True if the clause is a tautology, False otherwise.
    """
    return any(-lit in clause for lit in clause)


# Use filter and lambda to remove tautological clauses
def first_rule(clauses: CNF) -> CNF:
    """
    Rule 1: Remove tautologies from the CNF.

    :param clauses: The current CNF.
    :return: CNF without tautological clauses.
    """
    return set(filter(lambda c: not is_tautology(c), clauses))


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
        try:
            counter = [0]
            file_clauses = read_cnf(cnf_file)
            logger.info(f'Starting DP with clauses from {cnf_file}')
            start_time = time.time()
            file_clauses = first_rule(file_clauses) # We remove tautologies only once
            satisfiable = algorithm(file_clauses, counter=counter, logger=logger)
            end_time = time.time()
            logger.info(
                f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} '
                f'in {end_time - start_time:.3f} seconds.'
                f' DP called {counter[0]} times.'
            )
            sum_times += end_time - start_time
        except FileNotFoundError:
            logger.error(f'File not found: {cnf_file}')
        except Exception as e:
            logger.error(f'An error occurred while processing {cnf_file}: {e}')
    return sum_times