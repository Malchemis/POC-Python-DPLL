from typing import Set, Dict, List

from utils import CNF, Clause, Literal

class Formula:
    """
    A Formula encapsulates:
      - A list of clauses, each clause is a set of int-literals (e.g. {1, -3}).
      - A boolean 'active_clauses[cid]' indicating if a clause is still active.
      - A dictionary occurrences[literal] -> set of clauseIDs that contain 'literal'.
      - A dictionary frequency[literal] -> number of active clauses containing 'literal'.
      - watchers[clauseID] = list of up to two watched literals for that clause.
    """

    def __init__(self, list_of_clauses: List[Set[Literal]]):
        """
        Build the formula data structure from a list of clauses (each a set of int-literals).
        """
        self.clauses = list_of_clauses  # clauseID -> set of literals
        self.n_clauses = len(list_of_clauses)

        # Marks whether each clause is still active (not satisfied / not removed).
        self.active_clauses = [True] * self.n_clauses

        # occurrences[lit] = set of clauseIDs where 'lit' appears
        self.occurrences: Dict[Literal, Set[int]] = {}

        # watchers[cid] = [lit1, lit2] (the 2 watched literals for that clause),
        # or [lit] if only one literal remains, or [] if empty.
        self.watchers: List[List[int]] = [[] for _ in range(self.n_clauses)]

        # frequency[lit] = count of how many active clauses contain 'lit'.
        self.frequency: Dict[Literal, int] = {}

        self._init_data_structures()

    def _init_data_structures(self):
        """
        Initialize occurrences, watchers, and frequency once at the start.
        Also remove tautologies in place.
        """
        for cid, clause in enumerate(self.clauses):
            # Remove tautology if it appears
            if any(-lit in clause for lit in clause):
                # Mark clause as inactive
                self.active_clauses[cid] = False
                continue

            # Fill occurrences and frequency
            for lit in clause:
                if lit not in self.occurrences:
                    self.occurrences[lit] = set()
                self.occurrences[lit].add(cid)

                self.frequency[lit] = self.frequency.get(lit, 0) + 1

            # Initialize watchers: pick up to 2 watchers
            # The idea is that we don't need to scan a clause every time, we only do it when a watched literal changes.
            # We'll pick the first two literals we find, or just one if there's only one.
            # We can detect early termination, unit propagation, etc. by watching literals and their changes.
            if len(clause) >= 2:
                c_list = list(clause)
                self.watchers[cid] = [c_list[0], c_list[1]] # watch the first two literals
            elif len(clause) == 1:
                # Only one literal => watch it
                the_lit = next(iter(clause))
                self.watchers[cid] = [the_lit]

    def is_empty(self) -> bool:
        """
        True if no active clauses remain (i.e., everything is satisfied).
        """
        return not any(self.active_clauses)

    def has_empty_clause(self) -> bool:
        """
        True if there is any active clause that is empty => unsatisfiable.
        """
        for cid, active in enumerate(self.active_clauses):
            if active and len(self.clauses[cid]) == 0:
                return True
        return False

    def pure_literals(self) -> List[Literal]:
        """
        Returns a list of all 'pure' literals among the active clauses.
        A literal L is pure if -L does not appear in any active clause.
        """
        result = []
        # We'll examine all known literals in occurrences
        for lit, cset in self.occurrences.items(): # occurrences are literals -> set of clauseIDs
            if not cset:
                continue  # no active clauses contain lit

            # If the negation doesn't appear or appears in no active clauses => pure
            neg = -lit
            if neg not in self.occurrences or len(self.occurrences[neg]) == 0:
                # also ensure lit actually appears in some active clause
                # (meaning 'cset' isn't empty)
                if len(cset) > 0:
                    result.append(lit)
        return result

    def pick_branch_literal(self) -> int:
        """
        Heuristic: pick the literal with the highest frequency among those
        that actually appear in both polarities (so it's a real branch).

        Returns 0 if no branching literal can be found (likely formula simplified).
        """
        best_lit = 0
        best_count = -1

        for lit, freq in self.frequency.items(): # frequency is literal -> count
            if freq > best_count:
                # Only consider lit if its negation is also active in at least one clause
                if (lit != 0) and (-lit in self.frequency) and self.frequency[-lit] > 0:
                    best_lit = lit
                    best_count = freq

        return best_lit

    def assign_literal(self, lit: int) -> List[int]:
        """
        Assign 'lit' = True. This:
          - Satisfies all clauses containing lit => mark them inactive
          - Removes '-lit' from any clauses that contain it
          - Updates watchers, occurrences, frequency
        Returns a list of newly-unit literals discovered by this assignment.
        """
        newly_unit = []

        # 1) Deactivate all clauses satisfied by lit
        if lit in self.occurrences:
            satisfied_ids = list(self.occurrences[lit]) # Get a copy of the set of clauseIDs where lit appears
            for cid in satisfied_ids:
                if self.active_clauses[cid]:
                    # Mark clause as inactive
                    self.active_clauses[cid] = False
                    # Decrement frequency for all literals in that clause
                    for l in self.clauses[cid]:
                        if l in self.frequency:
                            self.frequency[l] = max(0, self.frequency[l] - 1)

                    # Also remove 'cid' from each literal's occurrences
                    for l in self.clauses[cid]:
                        if cid in self.occurrences.get(l, set()):
                            self.occurrences[l].discard(cid)

            # Clear occurrences[lit], as those clauses are now gone
            self.occurrences[lit].clear()

        # 2) Remove '-lit' from all clauses that contain it
        neg_lit = -lit
        if neg_lit in self.occurrences:
            clauses_with_neg = list(self.occurrences[neg_lit]) # Get a copy of the set of clauseIDs where -lit appears
            for cid in clauses_with_neg:
                # Only process active clauses
                if not self.active_clauses[cid]:
                    continue
                clause = self.clauses[cid] # Get the relevant active clause

                # Remove -lit in-place
                if neg_lit in clause:
                    # Remove the literal
                    clause.discard(neg_lit)
                    # Adjust frequency
                    if neg_lit in self.frequency:
                        self.frequency[neg_lit] = max(0, self.frequency[neg_lit] - 1)
                    self.occurrences[neg_lit].discard(cid)

                    # If that neg_lit was watched, pick a new watch. This is the only costly operation here.
                    if neg_lit in self.watchers[cid]:
                        w = self.watchers[cid]
                        idx = w.index(neg_lit)
                        # find a new literal in the clause to watch
                        new_watch = None
                        for x in clause:
                            if x not in w:
                                new_watch = x
                                break
                        if new_watch is not None:
                            w[idx] = new_watch
                        else:
                            # watchers might reduce to single-literal or empty
                            self.watchers[cid] = list(clause)

                    # if clause is now unit => record the unit literal
                    if len(clause) == 1:
                        only_lit = next(iter(clause))
                        newly_unit.append(only_lit)

        # We return the list of newly unit literals so that they can be propagated
        return newly_unit


class DPLLSolver:
    """
    A solver that implements DPLL with in-place updates, occurrence lists, watchers,
    and incremental frequency counting.
    """

    def __init__(self, formula: Formula, logger=None):
        self.formula = formula
        self.logger = logger

    def solve_dpll(self, counter: List[int]) -> bool:
        """
        Solve via DPLL. Return True if satisfiable, False if unsatisfiable.
        The 'counter[0]' is incremented in each top-level call or recursion,
        so we have a measure of how many times we enter the solver.
        """
        counter[0] += 1
        # Quick checks
        if self.formula.has_empty_clause():
            return False
        if self.formula.is_empty():
            return True

        # 1) Unit propagation
        if not self.unit_propagation(): # unit propagation might find a conflict
            return False
        if self.formula.is_empty():
            return True

        # 2) Pure literal elimination (repeat until no more pure literals appear)
        changed = True
        while changed:
            changed = False
            pures = self.formula.pure_literals()
            if pures:
                changed = True
                for p in pures:
                    # Assign pure literal
                    conflict_free = self.assign_lit(p) # returns False if conflict
                    if not conflict_free: # conflict detected
                        return False
                if self.formula.is_empty():
                    return True

        # 3) Check again after simplifications
        if self.formula.has_empty_clause():
            return False
        if self.formula.is_empty():
            return True

        # 4) Branching
        chosen_lit = self.formula.pick_branch_literal()
        if chosen_lit == 0:
            # No branching candidate => formula might be satisfied
            return True

        # Branch 1: chosen_lit = True
        saved_state = self._save_state()
        if self.assign_lit(chosen_lit):
            if self.solve_dpll(counter):
                return True
        self._restore_state(saved_state)

        # Branch 2: chosen_lit = False
        saved_state = self._save_state()
        if self.assign_lit(-chosen_lit):
            if self.solve_dpll(counter):
                return True
        self._restore_state(saved_state)

        return False

    def unit_propagation(self) -> bool:
        """
        Repeatedly look for unit clauses and assign them.
        Returns False if a conflict arises, True otherwise.
        """
        changed = True
        while changed:
            changed = False
            for cid, active in enumerate(self.formula.active_clauses):
                if not active:
                    continue
                clause = self.formula.clauses[cid]
                if len(clause) == 0:
                    # Conflict
                    return False
                if len(clause) == 1:
                    # Unit
                    unit_lit = next(iter(clause))
                    res = self.assign_lit(unit_lit)
                    if not res:
                        return False
                    changed = True
                    break  # re-start scanning
        return True

    def assign_lit(self, lit: int) -> bool:
        """
        Assign 'lit' = True. If this causes an empty clause => conflict => return False.
        Otherwise, True. Also propagate newly formed units.
        """
        new_units = self.formula.assign_literal(lit)

        # Now propagate those newly formed unit clauses
        i = 0
        while i < len(new_units):
            u = new_units[i]
            sub_new_units = self.formula.assign_literal(u)
            if self.formula.has_empty_clause():
                return False
            new_units.extend(sub_new_units)
            i += 1

        if self.formula.has_empty_clause():
            return False
        return True

    def _save_state(self):
        """
        Naive 'snapshot' for backtracking.
        In a serious solver, you'd keep a more incremental undo stack.
        """
        active_copy = list(self.formula.active_clauses)
        clause_copy = [set(cl) for cl in self.formula.clauses]
        occ_copy = {lit: set(s) for lit, s in self.formula.occurrences.items()}
        freq_copy = dict(self.formula.frequency)
        watch_copy = [list(w) for w in self.formula.watchers]
        return active_copy, clause_copy, occ_copy, freq_copy, watch_copy

    def _restore_state(self, saved):
        """
        Restore from snapshot.
        """
        (a, c, o, f, w) = saved
        self.formula.active_clauses = a
        self.formula.clauses = c
        self.formula.occurrences = o
        self.formula.frequency = f
        self.formula.watchers = w


def dpll(clauses: CNF, counter, logger=None) -> bool:
    """
    External interface matching your original signature:
      - clauses: a set of frozenset, each frozenset = a clause
      - counter: a list with counter[0] used for counting calls
      - logger: optional logger

    Returns True if satisfiable, False otherwise.
    """
    # Apply once tautology elimination and 4th rule (subsumption)
    clauses = fourth_rule(first_rule(clauses), changed=[False])

    # Convert set[frozenset] => list[set[int]] for in-place manipulations
    list_of_clauses = []
    for clause in clauses:
        # Convert each frozenset into a normal Python set
        list_of_clauses.append(set(clause))

    formula = Formula(list_of_clauses)
    solver = DPLLSolver(formula, logger=logger)
    result = solver.solve_dpll(counter)
    return result


### COPIED FROM dp.py ###
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