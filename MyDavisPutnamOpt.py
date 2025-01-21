import logging
import time
from typing import List, Set, Dict, FrozenSet
from functools import lru_cache
import cProfile
import pstats
import io

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Type aliases for clarity
Literal = int
Clause = FrozenSet[Literal]
CNF = Set[Clause]


def is_tautology(clause: Clause) -> bool:
    """
    Check if a clause is a tautology (contains a literal and its negation).

    :param clause: A frozenset representing a clause.
    :return: True if the clause is a tautology, False otherwise.
    """
    return any(-lit in clause for lit in clause)


# NOT USED, WE USE FILTERING ON THE FROZENSET INSTEAD
def first_rule(clauses: CNF) -> CNF:
    """
    Rule 1: Remove tautologies from the CNF.

    :param clauses: The current CNF.
    :return: CNF without tautological clauses.
    """
    filtered_clauses = {clause for clause in clauses if not is_tautology(clause)}
    if filtered_clauses != clauses:
        logger.debug("Rule 1 activated: Tautologies removed.")
    return filtered_clauses


def remove_value_from_clauses(clauses: CNF, value: Literal) -> CNF:
    """
    Remove a specific literal from all clauses.

    :param clauses: The current CNF.
    :param value: The literal to remove.
    :return: CNF with the literal removed from all clauses.
    """
    return {clause - {value} for clause in clauses}


def remove_clauses_with_value(clauses: CNF, value: Literal) -> CNF:
    """
    Remove all clauses that contain a specific literal.

    :param clauses: The current CNF.
    :param value: The literal to filter out.
    :return: CNF without clauses containing the specified literal.
    """
    return {clause for clause in clauses if value not in clause}


def find_pure_literals(clauses: CNF) -> Set[Literal]:
    """
    Find all pure literals in the CNF (literals that appear with only one polarity).

    :param clauses: The current CNF.
    :return: A set of pure literals.
    """
    literal_counts: Dict[Literal, int] = {}
    for clause in clauses:
        for literal in clause:
            literal_counts[literal] = literal_counts.get(literal, 0) + 1

    pure_literals = {lit for lit in literal_counts if -lit not in literal_counts}
    return pure_literals


def find_unit_clauses(clauses: CNF) -> Set[Literal]:
    """
    Find all unit literals in the CNF (literals in unit clauses).

    :param clauses: The current CNF.
    :return: A set of unit literals.
    """
    return {next(iter(clause)) for clause in clauses if len(clause) == 1}


def find_best_literal(clauses: CNF) -> Literal:
    """
    Heuristic to choose the best literal to branch on.
    Here, we choose the literal that appears most frequently.

    :param clauses: The current CNF.
    :return: The chosen literal.
    """
    literal_frequency: Dict[Literal, int] = {}
    for clause in clauses:
        for literal in clause:
            literal_frequency[literal] = literal_frequency.get(literal, 0) + 1

    if not literal_frequency:
        return 0

    # Choose the literal with the highest frequency
    best_literal = max(literal_frequency, key=literal_frequency.get)
    return best_literal


@lru_cache(maxsize=None)
def dp(clauses: FrozenSet[Clause]) -> bool:
    """
    DP algorithm to determine if the clauses are satisfiable.

    :param clauses: A frozenset representing the current CNF.
    :return: True if satisfiable, False otherwise.
    """
    global counter
    counter += 1

    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True

    if any(len(clause) == 0 for clause in clauses):
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply Rule 1: Remove tautologies
    clauses = set(filter(lambda c: not is_tautology(c), clauses))
    if not clauses:
        logger.debug("Success: All clauses satisfied after Rule 1.")
        return True
    if any(len(clause) == 0 for clause in clauses):
        logger.debug("Failure: Encountered an empty clause after Rule 1.")
        return False

    # Apply Rule 2: Unit Clause Elimination
    unit_literals = find_unit_clauses(clauses)
    while unit_literals:
        for unit in unit_literals:
            logger.debug(f"Rule 2 activated: Unit literal {unit}.")
            clauses = remove_clauses_with_value(clauses, unit)
            clauses = remove_value_from_clauses(clauses, -unit)
            if not clauses:
                logger.debug("Success: All clauses satisfied after Rule 2.")
                return True
            if any(len(clause) == 0 for clause in clauses):
                logger.debug("Failure: Encountered an empty clause after Rule 2.")
                return False
        unit_literals = find_unit_clauses(clauses)

    # Apply Rule 3: Pure Literal Elimination
    pure_literals = find_pure_literals(clauses)
    if pure_literals:
        for pure in pure_literals:
            logger.debug(f"Rule 3 activated: Pure literal {pure}.")
            clauses = remove_clauses_with_value(clauses, pure)
        if not clauses:
            logger.debug("Success: All clauses satisfied after Rule 3.")
            return True
        if any(len(clause) == 0 for clause in clauses):
            logger.debug("Failure: Encountered an empty clause after Rule 3.")
            return False

    # Choose the best literal to branch on
    chosen_literal = find_best_literal(clauses)
    if chosen_literal == 0:
        # No literals left, check if all clauses are satisfied
        return True

    logger.debug(f"Branching on literal {chosen_literal}.")

    # Branch 1: Assume chosen_literal is True
    new_clauses1 = remove_clauses_with_value(clauses, chosen_literal)
    new_clauses1 = remove_value_from_clauses(new_clauses1, -chosen_literal)

    # Branch 2: Assume chosen_literal is False
    new_clauses2 = remove_clauses_with_value(clauses, -chosen_literal)
    new_clauses2 = remove_value_from_clauses(new_clauses2, chosen_literal)

    # Recursive DP calls
    result1 = dp(frozenset(new_clauses1))
    if result1:
        return True

    result2 = dp(frozenset(new_clauses2))
    return result2


def read_cnf(file_path: str) -> FrozenSet[Clause]:
    """
    Read a CNF file in DIMACS format and return a set of clauses.

    :param file_path: Path to the CNF file.
    :return: A frozenset of frozensets, where each inner frozenset represents a clause.
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
    return frozenset(clauses)


def list_to_dimacs(clauses: List[List[Literal]]) -> str:
    """
    Convert a list of clauses to DIMACS CNF format.

    :param clauses: List of clauses.
    :return: A string in DIMACS CNF format.
    """
    num_clauses = len(clauses)
    all_literals = {lit for clause in clauses for lit in clause}
    num_vars = max(abs(lit) for lit in all_literals) if all_literals else 0
    dimacs = f"p cnf {num_vars} {num_clauses}\n"
    for clause in clauses:
        dimacs += ' '.join(map(str, clause)) + " 0\n"
    logger.info(f'DIMACS CNF:\n{dimacs}')
    return dimacs


def run_dp_on_files(cnf_files: List[str]) -> None:
    """
    Run the DP algorithm on a list of CNF files.

    :param cnf_files: List of file paths to CNF files.
    """
    global counter
    for cnf_file in cnf_files:
        try:
            counter = 0
            file_clauses = read_cnf(cnf_file)
            logger.info(f'Starting DP with clauses from {cnf_file}')
            start_time = time.time()
            satisfiable = dp(file_clauses)
            end_time = time.time()
            logger.info(
                f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} '
                f'in {end_time - start_time:.2f} seconds.'
                f' DP called {counter} times.'
            )
        except FileNotFoundError:
            logger.error(f'File not found: {cnf_file}')
        except Exception as e:
            logger.error(f'An error occurred while processing {cnf_file}: {e}')


def main():
    # Folder names for SAT and NON-SAT problems
    sat_folder = 'uf50'
    non_sat_folder = 'uuf50'

    # Example usage with multiple CNF files
    cnf_files = [
        f'{sat_folder}/uf50-01.cnf',
        f'{non_sat_folder}/uuf50-01.cnf',
        f'{sat_folder}/uf50-010.cnf',
        f'{non_sat_folder}/uuf50-010.cnf',
        'uf175-01.cnf',
        'uuf150-01.cnf'
    ]

    run_dp_on_files(cnf_files)


if __name__ == '__main__':
    # Create a profiler
    profiler = cProfile.Profile()
    profiler.enable()

    counter = 0
    main()

    profiler.disable()

    # Create a stream to capture the profiling data
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()

    # Output the profiling results to a file
    with open("profiling_results.txt", "w") as f:
        f.write(s.getvalue())

    print(s.getvalue())

