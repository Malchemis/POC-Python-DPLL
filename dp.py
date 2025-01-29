from typing import Set, Dict  # Type hints for better readability and error checking

from utils import Literal, Clause, CNF  # Import the custom types


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
def remove_value_from_clauses(clauses: CNF, value: Literal, changed: list) -> CNF:
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
            changed[0] = True
        else:
            new_clauses.add(clause)
    return new_clauses


def remove_clauses_with_value(clauses: CNF, value: Literal, changed: list) -> CNF:
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
            changed[0] = True  # Mark change if a clause is removed
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


def fourth_rule(clauses: CNF, changed: list) -> CNF:
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
                    changed[0] = True  # Mark that a change occurred

    return new_clauses


# To fasten the search and pick the best literal to branch on,
# we use a dictionary to count the occurrences of each literal
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

    # If there are no literals, return 0
    if not literal_frequency:
        return 0

    # Filter on literals l with both polarities
    # we want to branch on world1 where l is True and world2 where l is False
    for literal in list(literal_frequency.keys()):
        if -literal not in literal_frequency:
            del literal_frequency[literal]

    # If there are no literals, return 0
    if not literal_frequency:
        return 0

    # Choose the literal with the highest frequency
    best_literal = max(literal_frequency, key=literal_frequency.get)
    return best_literal


def dp(clauses: CNF, counter, logger) -> bool:
    """
    DP algorithm to determine if the clauses are satisfiable.
    For the order of the rules and the branching, we follow the DP pseudocode
    at https://en.wikipedia.org/wiki/Davis%E2%80%93Putnam_algorithm

    :param clauses: A set representing the current CNF.
    :param counter: A list container of a counter to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :return: True if satisfiable, False otherwise.
    """
    changed = [False] # Pass the boolean by reference
    counter[0] += 1

    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if any(not clause for clause in clauses):
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

    if changed[0]:
        return dp(clauses, counter, logger)
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if any(not clause for clause in clauses):
        logger.debug("Failure: Encountered an empty clause.")
        return False


    # Apply Third Rule: Pure Literal Elimination
    pure_literals = find_pure_literals(clauses)
    if pure_literals:
        for pure in pure_literals:
            logger.debug(f"Rule 3 activated: Pure literal {pure}.")
            clauses = remove_clauses_with_value(clauses, pure, changed)
        if changed[0]:
            return dp(clauses, counter, logger)
        if not clauses:
            logger.debug("Success: All clauses satisfied.")
            return True
        if any(not clause for clause in clauses):
            logger.debug("Failure: Encountered an empty clause.")
            return False


    # Apply the 4th Rule: If a clause is a superset of another clause, remove the superset clause.
    clauses = fourth_rule(clauses, changed)
    if changed[0]:
        return dp(clauses, counter, logger)
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if any(not clause for clause in clauses):
        logger.debug("Failure: Encountered an empty clause.")
        return False


    # Apply Davis Putnam Branching : If lit and not(lit) are in the clauses, we can branch
    chosen_literal = find_best_literal(clauses)
    if chosen_literal == 0:
        logger.debug("No literals left, check if all clauses are satisfied")
        return True

    logger.debug(f"Branching on literal {chosen_literal}.")
    # Branch 1: Assume chosen_literal is True
    new_clauses1 = remove_clauses_with_value(clauses, chosen_literal, changed)
    new_clauses1 = remove_value_from_clauses(new_clauses1, -chosen_literal, changed)
    # Branch 2: Assume chosen_literal is False
    new_clauses2 = remove_clauses_with_value(clauses, -chosen_literal, changed)
    new_clauses2 = remove_value_from_clauses(new_clauses2, chosen_literal, changed)

    # Recursive DP calls
    return dp(new_clauses1, counter, logger) or dp(new_clauses2, counter, logger)


def dpll(clauses: CNF, counter, logger=None) -> (bool, int):
    """
    DPLL algorithm to determine if the CNF is satisfiable. Similar to DP, but fewer rules.
    - Only unit propagation and pure literal elimination are used.
    - Rule4 is used only once at the beginning (as there is less and less chance of it being useful).

    :param clauses: A set representing the current CNF.
    :param counter: A list container of a counter to keep track of the recursive calls.
    :param logger: The logger object to log messages.
    :return: True if satisfiable, False otherwise, and the number of recursive calls.
    """
    # Stopping conditions
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if any(not clause for clause in clauses):
        logger.debug("Failure: Encountered an empty clause.")
        return False

    # Apply Rule 1: Remove tautologies
    clauses = first_rule(clauses)

    # Apply Rule 4: Remove clauses that are supersets of other clauses
    clauses = fourth_rule(clauses, [False])
    return dpll_helper(clauses, counter, logger)


def dpll_helper(clauses: CNF, counter, logger=None) -> (bool, int):
    """
    DPLL algorithm to determine if the CNF is satisfiable. Similar to DP, but fewer rules.
    - Only unit propagation and pure literal elimination are used.
    - Rule4 is used only once at the beginning (as there is less and less chance of it being useful).

    :param clauses: A set representing the current CNF.
    :param counter: A list container of a counter to keep track of recursive calls.
    :param logger: The logger object to log messages.
    :return: True if satisfiable, False otherwise, and the number of recursive calls.
    """
    changed = [False]  # Pass the boolean
    counter[0] += 1

    # Stopping conditions
    if not clauses:
        logger.debug("Success: All clauses satisfied.")
        return True
    if any(not clause for clause in clauses):
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
    if any(not clause for clause in clauses):
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
        if any(not clause for clause in clauses):
            logger.debug("Failure: Encountered an empty clause.")
            return False

    # Branching
    chosen_literal = find_best_literal(clauses)
    if chosen_literal == 0:
        logger.debug("No literals left, check if all clauses are satisfied")
        return True

    logger.debug(f"Branching on literal {chosen_literal}.")
    # Branch 1: Assume chosen_literal is True
    new_clauses1 = remove_clauses_with_value(clauses, chosen_literal, changed)
    new_clauses1 = remove_value_from_clauses(new_clauses1, -chosen_literal, changed)
    # Branch 2: Assume chosen_literal is False
    new_clauses2 = remove_clauses_with_value(clauses, -chosen_literal, changed)
    new_clauses2 = remove_value_from_clauses(new_clauses2, chosen_literal, changed)

    # Recursive calls
    return dpll_helper(new_clauses1, counter, logger) or dpll_helper(new_clauses2, counter, logger)


def classical_dpll(clauses, counter, logger=None):
    """
    Naive DPLL:
      - clauses: set of frozensets
      - returns True/False for satisfiability.
    """

    counter[0] += 1  # counting calls

    # 1) If no clauses => satisfiable
    if not clauses:
        return True

    # 2) If any empty clause => unsatisfiable
    if any(len(cl) == 0 for cl in clauses):
        return False

    # 3) Unit propagation
    unit_literals = {next(iter(c)) for c in clauses if len(c) == 1}
    while unit_literals:
        for u in unit_literals:
            # remove all clauses containing u
            clauses = {c for c in clauses if u not in c}
            # remove ¬u from remaining clauses
            clauses = {frozenset(x for x in c if x != -u) for c in clauses}
        # re-check for new units
        if any(len(cl) == 0 for cl in clauses):
            return False
        unit_literals = {next(iter(c)) for c in clauses if len(c) == 1}

    if not clauses:
        return True

    # 4) Pick a literal to branch on
    lit = next(iter(next(iter(clauses)))) # First literal of the first clause

    # Branch: lit = True
    new_clauses = {c for c in clauses if lit not in c}
    new_clauses = {frozenset(x for x in c if x != -lit) for c in new_clauses}
    if classical_dpll(new_clauses, counter, logger):
        return True

    # Branch: lit = False
    new_clauses = {c for c in clauses if -lit not in c}
    new_clauses = {frozenset(x for x in c if x != lit) for c in new_clauses}
    return classical_dpll(new_clauses, counter, logger)
