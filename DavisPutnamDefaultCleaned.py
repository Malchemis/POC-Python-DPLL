import logging
import time
# import cProfile
# import pstats
# import io


def is_tautology(clause: list) -> bool:
    """
    Return True if the list of integers contains an integer and its opposite.

    :param clause: List of integers representing a clause.
    :return: True if the clause contains a literal and its negation, otherwise False.
    """
    for literal in clause:
        if -literal in clause:
            return True
    return False


def first_rule(clauses: list) -> list:
    """
    Rule 1: Remove tautologies from the list of clauses.

    :param clauses: List of clauses.
    :return: List of clauses without tautologies.
    """
    filtered_clauses = [clause for clause in clauses if not is_tautology(clause)]
    if filtered_clauses != clauses:
        logger.debug("Rule 1 activated: Tautologies removed.")
    return filtered_clauses


def test_first_rule():
    l1 = [[1, 2], [1, 4, -1], [8, 1, 6, 4, 9, 1, -6], [-2, 4], [1]]
    logger.info(f'Before first rule: {l1}')
    l2 = first_rule(l1)
    logger.info(f'After first rule (tautology removed): {l2}')


def remove_value_from_clauses(clauses: list, value: int) -> list:
    """
    Remove a specific value from all clauses.

    :param clauses: List of clauses.
    :param value: The value to remove.
    :return: List of clauses with the value removed.
    """
    return [[literal for literal in clause if literal != value] for clause in clauses]


def remove_clauses_with_value(clauses: list, value: int) -> list:
    """
    Remove all clauses that contain a specific value.

    :param clauses: List of clauses.
    :param value: The value to filter out.
    :return: List of clauses without the specified value.
    """
    return [clause for clause in clauses if value not in clause]


def second_rule(clauses: list) -> list:
    """
    Rule 2: If a clause contains a single literal, remove all clauses containing that literal
    and remove the negation of that literal from other clauses.

    :param clauses: List of clauses.
    :return: Updated list of clauses after applying Rule 2.
    """
    for clause in clauses:
        if len(clause) == 1:
            value = clause[0]
            clauses = remove_clauses_with_value(clauses, value)
            clauses = remove_value_from_clauses(clauses, -value)
            logger.debug(f'Rule 2 activated: Removed clauses containing {value} and -{value} from others.')
            return clauses
    return clauses


def test_second_rule():
    l2 = [[1], [1, 2], [1, 6, 4], [-2, 4], [-1, 7]]
    logger.info(f'Before second rule: {l2}')
    l3 = second_rule(l2)
    logger.info(f'After second rule (single literal removed): {l3}')


def exists_in_clauses(value: int, clauses: list) -> bool:
    """
    Check if a value exists in any of the clauses.

    :param value: The value to check.
    :param clauses: List of clauses.
    :return: True if the value exists in any clause, otherwise False.
    """
    return any(value in clause for clause in clauses)


def find_single_literal(clauses: list) -> int:
    """
    Find a literal that appears in clauses but its negation does not appear in any clause.

    :param clauses: List of clauses.
    :return: The single literal if found, otherwise 0.
    """
    for clause in clauses:
        for literal in clause:
            if not exists_in_clauses(-literal, clauses):
                return literal
    return 0


def third_rule(clauses: list) -> list:
    """
    Rule 3: If a literal appears in clauses and its negation does not, remove all clauses containing that literal.

    :param clauses: List of clauses.
    :return: Updated list of clauses after applying Rule 3.
    """
    literal = find_single_literal(clauses)
    if literal != 0:
        clauses = remove_clauses_with_value(clauses, literal)
        logger.debug(f'Rule 3 activated: Removed clauses containing {literal}.')
    return clauses


def test_third_rule():
    l3 = [[1, 2], [1, 6, 4], [-2, 4]]
    logger.info(f'Before third rule: {l3}')
    l4 = third_rule(l3)
    logger.info(f'After third rule (single literal processed): {l4}')


def find_superset_clauses(clauses: list) -> list:
    """
    Find clauses that are supersets of other clauses.

    :param clauses: List of clauses.
    :return: List of clauses that are supersets.
    """
    supersets = []
    for clause in clauses:
        for other_clause in clauses:
            if clause != other_clause and all(elem in clause for elem in other_clause):
                supersets.append(clause)
                break
    return supersets


def fourth_rule(clauses: list) -> list:
    """
    Rule 4: If a clause is a superset of another clause, remove the superset clause.

    :param clauses: List of clauses.
    :return: Updated list of clauses after applying Rule 4.
    """
    supersets = find_superset_clauses(clauses)
    clauses = [clause for clause in clauses if clause not in supersets]
    if supersets:
        logger.debug(f'Rule 4 activated: Removed supersets {supersets}.')
    return clauses


def test_fourth_rule():
    l4 = [[1, 2], [1, 6, 4], [1, 2, 4], [1, 6]]
    logger.info(f'Before fourth rule: {l4}')
    l5 = fourth_rule(l4)
    logger.info(f'After fourth rule (supersets removed): {l5}')


def find_non_single_literal(clauses: list) -> int:
    """
    Find a literal whose negation also exists in the clauses.

    :param clauses: List of clauses.
    :return: The literal if found, otherwise 0.
    """
    for clause in clauses:
        for literal in clause:
            if exists_in_clauses(-literal, clauses):
                return literal
    return 0


def fifth_rule(clauses: list) -> tuple:
    """
    Rule 5: Create new branches by choosing a literal and splitting the problem into two sub-problems.

    :param clauses: List of clauses.
    :return: A tuple containing two lists of clauses representing the new branches.
    """
    literal = find_non_single_literal(clauses)
    if literal != 0:
        clauses_branch1 = remove_clauses_with_value(clauses, literal)
        clauses_branch1 = remove_value_from_clauses(clauses_branch1, -literal)

        clauses_branch2 = remove_clauses_with_value(clauses, -literal)
        clauses_branch2 = remove_value_from_clauses(clauses_branch2, literal)

        logger.debug(f'Rule 5 activated: Creating branches with {literal} and {-literal}.')
        return clauses_branch1, clauses_branch2
    return (), ()


def test_fifth_rule():
    l5 = [[1, 2], [1, 6, 4], [-1, 2, 4], [5, 6], [4, 5, -1]]
    logger.info(f'Before fifth rule: {l5}')
    branch1, branch2 = fifth_rule(l5)
    logger.info(f'After fifth rule (branches created):\nBranch 1: {branch1}\nBranch 2: {branch2}')


def formulas_equal(f1: list, f2: list) -> bool:
    """
    Check if two formulas (lists of clauses) are identical.

    :param f1: First formula.
    :param f2: Second formula.
    :return: True if both formulas are identical, otherwise False.
    """
    if len(f1) != len(f2):
        return False
    for clause in f1:
        if clause not in f2:
            return False
    return True


def dp(clauses: list) -> bool:
    """
    DP algorithm to determine if the clauses are satisfiable.

    :param clauses: List of clauses.
    :return: True if satisfiable, False otherwise.
    """
    global counter
    counter += 1
    logger.debug(f'Resolving clauses: {clauses}')

    # Apply Rule 1
    clauses = first_rule(clauses)
    if not clauses:
        logger.info("Success: All clauses satisfied.")
        return True
    if [] in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply Rule 2
    clauses = second_rule(clauses)
    if not clauses:
        logger.info("Success: All clauses satisfied after Rule 2.")
        return True
    if [] in clauses:
        logger.debug("Failure: Encountered an empty clause after Rule 2.")
        return False
    if not formulas_equal(first_rule(clauses), clauses):
        return dp(clauses)

    # Apply Rule 3
    clauses = third_rule(clauses)
    if not clauses:
        logger.info("Success: All clauses satisfied after Rule 3.")
        return True
    if [] in clauses:
        logger.debug("Failure: Encountered an empty clause after Rule 3.")
        return False
    if not formulas_equal(second_rule(clauses), clauses):
        return dp(clauses)

    # Apply Rule 4
    clauses = fourth_rule(clauses)
    if not clauses:
        logger.info("Success: All clauses satisfied after Rule 4.")
        return True
    if [] in clauses:
        logger.debug("Failure: Encountered an empty clause after Rule 4.")
        return False
    if not formulas_equal(third_rule(clauses), clauses):
        return dp(clauses)

    # Apply Rule 5
    branch1, branch2 = fifth_rule(clauses)
    if branch1 or branch2:
        result = dp(branch1) or dp(branch2)
        logger.debug(f'Finished resolving clauses: {clauses}')
        return result

    logger.debug("Finished resolving clauses without finding a solution.")
    return False


def read_cnf(file_path: str) -> list:
    """
    Read a CNF file in DIMACS format and return a list of clauses.

    :param file_path: Path to the CNF file.
    :return: List of clauses where each clause is a list of integers.
    """
    clauses = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("%"):
                break
            if line.startswith('c') or line.startswith('p'):
                continue
            literals = list(map(int, line.strip().split()))
            if literals and literals[-1] == 0:
                literals.pop()
            if literals:
                clauses.append(literals)
    return clauses


def list_to_dimacs(clauses: list) -> str:
    """
    Convert a list of clauses to DIMACS CNF format.

    :param clauses: List of clauses.
    :return: A string in DIMACS CNF format.
    """
    num_clauses = len(clauses)
    all_literals = [literal for clause in clauses for literal in clause]
    num_vars = max(abs(lit) for lit in all_literals) if all_literals else 0
    dimacs = f"p cnf {num_vars} {num_clauses}\n"
    for clause in clauses:
        dimacs += ' '.join(map(str, clause)) + " 0\n"
    logger.info(f'DIMACS CNF:\n{dimacs}')
    return dimacs


def test_dimacs_conversion():
    clauses = [[1, 2], [-1, 3], [4, -5, 6]]
    logger.info(f'Original clauses: {clauses}')
    dimacs = list_to_dimacs(clauses)
    logger.info(f'Converted DIMACS:\n{dimacs}')


def main():
    # Main variables
    testing = False
    large_problems = True
    global counter

    # Folder names for SAT and UNSAT problems
    sat_folder = 'uf50'
    unsat_folder = 'uuf50'

    # Testing the rules
    if testing:
        test_first_rule()
        test_second_rule()
        test_third_rule()
        test_fourth_rule()
        test_fifth_rule()
        test_dimacs_conversion()

    # Small problems
    # Read CNF file and run DP
    cnf_file = f'{sat_folder}/uf50-01.cnf'
    clauses = read_cnf(cnf_file)
    counter = 0
    logger.info(f'Starting DP with clauses from {cnf_file}')
    start = time.time()
    satisfiable = dp(clauses)
    end = time.time()
    logger.info(f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')

    # Read CNF file and run DP
    cnf_file = f'{unsat_folder}/uuf50-01.cnf'
    clauses = read_cnf(cnf_file)
    counter = 0
    logger.info(f'Starting DP with clauses from {cnf_file}')
    start = time.time()
    satisfiable = dp(clauses)
    end = time.time()
    logger.info(f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')

    # Read CNF file and run DP
    cnf_file = f'{sat_folder}/uf50-010.cnf'
    clauses = read_cnf(cnf_file)
    counter = 0
    logger.info(f'Starting DP with clauses from {cnf_file}')
    start = time.time()
    satisfiable = dp(clauses)
    end = time.time()
    logger.info(
        f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')

    # Read CNF file and run DP
    cnf_file = f'{unsat_folder}/uuf50-010.cnf'
    clauses = read_cnf(cnf_file)
    counter = 0
    logger.info(f'Starting DP with clauses from {cnf_file}')
    start = time.time()
    satisfiable = dp(clauses)
    end = time.time()
    logger.info(
        f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')

    if large_problems:
        # Large problems
        # Read CNF file and run DP
        cnf_file = f'uf175-01.cnf'
        clauses = read_cnf(cnf_file)
        counter = 0
        logger.info(f'Starting DP with clauses from {cnf_file}')
        start = time.time()
        satisfiable = dp(clauses)
        end = time.time()
        logger.info(f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')

        # Read CNF file and run DP
        cnf_file = f'uuf150-01.cnf'
        clauses = read_cnf(cnf_file)
        counter = 0
        logger.info(f'Starting DP with clauses from {cnf_file}')
        start = time.time()
        satisfiable = dp(clauses)
        end = time.time()
        logger.info(f'Formula is {"satisfiable" if satisfiable else "unsatisfiable"} after {counter} steps in {end - start:.2f} seconds.')


if __name__ == '__main__':
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    counter = 0

    # # Create a profiler
    # profiler = cProfile.Profile()
    # profiler.enable()

    main()

    # profiler.disable()
    # s = io.StringIO()
    # sort_by = 'cumulative'
    # ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
    # ps.print_stats()
    #
    # # Output the profiling results to a file
    # with open("results/profiling_results_dp_default.txt", "w") as f:
    #     f.write(s.getvalue())
    #
    # print(s.getvalue())