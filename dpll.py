from typing import Set, Dict  # Type hints for better readability and error checking

from utils import Literal, Clause, CNF, ChangeTracker  # Import the custom types


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


# Take advantage of the set operations to remove the clauses with the unit literals
def remove_value_from_clauses(clauses: CNF, value: Literal, changed: ChangeTracker) -> CNF:
    """
    Remove a specific literal from all clauses and track changes.

    :param clauses: The current CNF.
    :param value: The literal to remove.
    :param changed: A list container of a boolean indicating if changes were made.
    :return: CNF with the literal removed.
    """
    new_clauses = set()
    for clause in clauses:
        if value in clause:
            new_clauses.add(clause - {value})
            changed.set_changed()  # Mark change if a literal is removed
        else:
            new_clauses.add(clause)
    return new_clauses


def remove_clauses_with_value(clauses: CNF, value: Literal, changed: ChangeTracker) -> CNF:
    """
    Remove all clauses that contain a specific literal and track changes.

    :param clauses: The current CNF.
    :param value: The literal to filter out.
    :param changed: A list container of a boolean indicating if changes were made.

    :return: CNF without clauses containing the specified literal.
    """
    new_clauses = set()
    for clause in clauses:
        if value not in clause:
            new_clauses.add(clause)
        else:
            changed.set_changed()  # Mark change if a clause is removed
    return new_clauses


# We use a dictionary to count the occurrences of each literal
def find_pure_literals(clauses: CNF) -> Set[Literal]:
    """
    Find all pure literals in the CNF (literals that appear with only one polarity).

    :param clauses: The current CNF.
    :return: A set of pure literals.
    """
    # Count the occurrences of each literal
    literal_counts: Dict[Literal, int] = {}
    for clause in clauses:
        for literal in clause:
            # Get value or default to 0, then increment
            literal_counts[literal] = literal_counts.get(literal, 0) + 1

    # Use a set comprehension to find the pure literals
    pure_literals = {lit for lit in literal_counts if -lit not in literal_counts}
    return pure_literals


# Here we take advantage of Iterable unpacking to get the first element of the clause
# We do this because we cannot index a set
def find_unit_clauses(clauses: CNF) -> Set[Literal]:
    """
    Find all unit literals in the CNF (literals in unit clauses).

    :param clauses: The current CNF.
    :return: A set of unit literals.
    """
    return {next(iter(clause)) for clause in clauses if len(clause) == 1}


def fourth_rule(clauses: CNF, changed: ChangeTracker) -> CNF:
    """
    Rule 4: Remove clauses that are supersets of other clauses.
    That is, if there is any clause d ⊂ c, we remove c.

    :param clauses: The current CNF.
    :param changed: A list container of a boolean indicating if changes were made.
    :return: CNF without clauses that are supersets of other clauses.
    """
    # Convert clauses to a sorted list (smallest clauses first) for efficient subset checks
    sorted_clauses = sorted(clauses, key=len)
    new_clauses = set(sorted_clauses)  # Start with all clauses

    for i, small_clause in enumerate(sorted_clauses):
        # Compare small_clause with all larger clauses that follow
        for larger_clause in sorted_clauses[i + 1:]:
            if small_clause < larger_clause:  # Proper subset check
                if larger_clause in new_clauses:
                    new_clauses.remove(larger_clause)
                    changed.set_changed()  # Mark change if a clause is removed

    return new_clauses


def find_best_literal(clauses: CNF, n_vars: int=500) -> int:
    # Arrays to hold counts for positive and negative occurrences.
    pos_counts = [0] * (n_vars + 1)  # index i for literal i
    neg_counts = [0] * (n_vars + 1)  # index i for literal -i

    # Single pass over the clauses
    for clause in clauses:
        for literal in clause:
            if literal > 0:
                pos_counts[literal] += 1
            else:
                neg_counts[-literal] += 1

    best_literal = 0
    best_score = -1

    # Only consider variables that appear in both polarities.
    for var in range(1, n_vars + 1):
        if pos_counts[var] and neg_counts[var]:
            score = pos_counts[var] + neg_counts[var]
            if score > best_score:
                best_score = score
                best_literal = var if pos_counts[var] >= neg_counts[var] else -var

    return best_literal


def dp(clauses: CNF, counter, logger, n_vars=0) -> bool:
    """
    DP algorithm to determine if the clauses are satisfiable.
    For the order of the rules and the branching, we follow the DP pseudocode
    at https://en.wikipedia.org/wiki/Davis%E2%80%93Putnam_algorithm

    :param clauses: A set representing the current CNF.
    :param counter: Counter object to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :param n_vars: The number of variables in the CNF.
    :return: True if satisfiable, False otherwise.
    """
    changed = ChangeTracker()  # Wrapper around a boolean to track changes
    counter.increment()

    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if frozenset() in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply the First Rule: Remove Tautologies
    clauses = first_rule(clauses)

    # Apply the Second Rule: Unit Clause Elimination // Unit Propagation
    unit_literals = find_unit_clauses(clauses)
    while unit_literals:
        for unit in unit_literals:
            logger.debug(f"Rule 2 activated: Unit literal {unit}.")
            clauses = remove_clauses_with_value(clauses, unit, changed)
            clauses = remove_value_from_clauses(clauses, -unit, changed)
        unit_literals = find_unit_clauses(clauses)

    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if frozenset() in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False
    if changed:
        return dp(clauses, counter, logger, n_vars)


    # Apply Third Rule: Pure Literal Elimination
    pure_literals = find_pure_literals(clauses)
    if pure_literals:
        for pure in pure_literals:
            logger.debug(f"Rule 3 activated: Pure literal {pure}.")
            clauses = remove_clauses_with_value(clauses, pure, changed)
        if not clauses:
            logger.debug("Success: All clauses satisfied.")
            return True
        if frozenset() in clauses:
            logger.debug("Failure: Encountered an empty clause.")
            return False
        if changed:
            return dp(clauses, counter, logger, n_vars)


    # Apply the 4th Rule: If a clause is a superset of another clause, remove the superset clause.
    clauses = fourth_rule(clauses, changed)
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if frozenset() in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False
    if changed:
        return dp(clauses, counter, logger, n_vars)


    # Apply Davis Putnam Branching : If lit and not(lit) are in the clauses, we can branch
    chosen_literal = find_best_literal(clauses)
    if chosen_literal == 0:
        logger.debug("No literals left, check if all clauses are satisfied")
        return True

    logger.debug(f"Branching on literal {chosen_literal}.")
    # Branch 1: Assume chosen_literal is True
    new_clauses1 = remove_clauses_with_value(clauses, chosen_literal, changed)
    new_clauses1 = remove_value_from_clauses(new_clauses1, -chosen_literal, changed)
    if dp(new_clauses1, counter, logger, n_vars):
        return True

    # Branch 2: Assume chosen_literal is False
    new_clauses2 = remove_clauses_with_value(clauses, -chosen_literal, changed)
    new_clauses2 = remove_value_from_clauses(new_clauses2, chosen_literal, changed)
    return dp(new_clauses2, counter, logger, n_vars)


def classical_dpll(clauses: CNF, counter, logger=None, n_vars=0) -> (bool, int):
    """
    DPLL algorithm to determine if the CNF is satisfiable.
    Similar to DP, but fewer rules.
    We do not use heuristics for branching.
     :param clauses: A set representing the current CNF.
    :param counter: A list container of a counter to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :param n_vars: The number of variables in the CNF.
    :return: True if satisfiable, False otherwise, and the number of recursive calls.
    """
    # Apply Rule 1: Remove tautologies
    clauses = first_rule(clauses)

    # Apply Rule 4: Remove clauses that are supersets of other clauses
    clauses = fourth_rule(clauses, ChangeTracker())
    # Heuristic: Take the first literal in the clause
    return dpll_helper(clauses, counter, logger, heuristic=lambda x, n: next(iter(next(iter(x)))), n_vars=n_vars)


def dpll(clauses: CNF, counter, logger=None, n_vars=0) -> (bool, int):
    """
    DPLL algorithm to determine if the CNF is satisfiable. Similar to DP, but fewer rules.
    - Only unit propagation and pure literal elimination are used.
    - Rule4 is used only once at the beginning (as there is less and less chance of it being useful).

    :param clauses: A set representing the current CNF.
    :param counter: A list container of a counter to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :param n_vars: The number of variables in the CNF.
    :return: True if satisfiable, False otherwise, and the number of recursive calls.
    """
    # Apply Rule 1: Remove tautologies
    clauses = first_rule(clauses)

    # Apply Rule 4: Remove clauses that are supersets of other clauses
    fourth_rule(clauses, ChangeTracker())
    return dpll_helper(clauses, counter, logger, heuristic=find_best_literal, n_vars=n_vars)


def dpll_helper(clauses: CNF, counter, logger=None, heuristic=find_best_literal, n_vars=0) -> (bool, int):
    """
    DPLL algorithm to determine if the CNF is satisfiable. Similar to DP, but fewer rules.
    - Only unit propagation and pure literal elimination are used.
    - Rule4 is used only once at the beginning (as there is less and less chance of it being useful).

    :param clauses: A set representing the current CNF.
    :param counter: Counter object to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :param heuristic: The function to choose the best literal to branch on.
    :param n_vars: The number of variables in the CNF.
    :return: True if satisfiable, False otherwise, and the number of recursive calls.
    """
    changed = ChangeTracker()  # Wrapper around a boolean to track changes
    counter.increment()

    # Stopping conditions
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if frozenset() in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply 2nd Rule : Unit propagation
    unit_literals = find_unit_clauses(clauses)
    while unit_literals:
        for unit in unit_literals:
            logger.debug(f"Rule 2 activated: Unit literal {unit}.")
            clauses = remove_clauses_with_value(clauses, unit, changed)
            clauses = remove_value_from_clauses(clauses, -unit, changed)
        unit_literals = find_unit_clauses(clauses)

    # Stopping conditions
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if frozenset() in clauses:
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply Third Rule: Pure Literal Elimination
    pure_literals = find_pure_literals(clauses)
    if pure_literals:
        for pure in pure_literals:
            logger.debug(f"Rule 3 activated: Pure literal {pure}.")
            clauses = remove_clauses_with_value(clauses, pure, changed)
        # Stopping conditions
        if not clauses:
            logger.debug("Success: All clauses satisfied.")
            return True
        if frozenset() in clauses:
            logger.debug("Failure: Encountered an empty clause.")
            return False
        if changed:
            return dpll_helper(clauses, counter, logger, heuristic, n_vars)

    # Branching
    chosen_literal = heuristic(clauses, n_vars)
    if chosen_literal == 0:
        logger.debug("No literals left, check if all clauses are satisfied")
        return True

    logger.debug(f"Branching on literal {chosen_literal}.")
    # Branch 1: Assume chosen_literal is True
    new_clauses1 = remove_clauses_with_value(clauses, chosen_literal, changed)
    new_clauses1 = remove_value_from_clauses(new_clauses1, -chosen_literal, changed)
    if dpll_helper(new_clauses1, counter, logger, heuristic, n_vars):
        return True

    # Branch 2: Assume chosen_literal is False
    new_clauses2 = remove_clauses_with_value(clauses, -chosen_literal, changed)
    new_clauses2 = remove_value_from_clauses(new_clauses2, chosen_literal, changed)
    return dpll_helper(new_clauses2, counter, logger, heuristic, n_vars)
