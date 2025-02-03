import heapq
from typing import Set, List
from utils import Counter

# Type aliases for clarity
Literal = int
Clause = Set[Literal]
CNF = List[Clause]


class Formula:
    """
    Represents a CNF formula and maintains auxiliary data structures to support an optimized DPLL algorithm.

    Attributes:
      - clauses: The list of clauses (each clause is a set of literals).
      - active_clauses: A boolean list where active_clauses[cid] is True if clause cid is still active.
      - pos_frequency: Fixed-size array; pos_frequency[i] is the count of occurrences of literal i.
      - neg_frequency: Fixed-size array; neg_frequency[i] is the count of occurrences of literal -i.
      - pos_occurrences: For literal i (> 0), a list of clause IDs where i appears.
      - neg_occurrences: For literal -i, a list of clause IDs where -i appears.
      - watchers: For each clause (by index), a list (of up to two) of "watched" literals.
                  The idea is to quickly determine when a clause becomes unit.
    """

    def __init__(self, list_of_clauses: CNF, n_vars: int):
        """
        Initialize the formula from a list of clauses.

        Parameters:
          - list_of_clauses: A list of clauses (each clause is a set of literals).
          - n_vars: The total number of variables in the formula.
        """
        self.n_vars: int = n_vars
        self.n_clauses: int = len(list_of_clauses)
        self.clauses: CNF = list_of_clauses
        self.active_clauses: List[bool] = [True] * self.n_clauses

        # Fixed-size arrays to count literal occurrences.
        self.pos_frequency: List[int] = [0] * (n_vars + 1)  # pos_frequency[i] for literal i (>0)
        self.neg_frequency: List[int] = [0] * (n_vars + 1)  # neg_frequency[i] for literal -i

        # Occurrence lists: for literal i (> 0) and literal -i.
        self.pos_occurrences: List[List[int]] = [[] for _ in range(n_vars + 1)]
        self.neg_occurrences: List[List[int]] = [[] for _ in range(n_vars + 1)]

        # Watchers: each clause has a list (of up to two) of watched literals.
        self.watchers: List[List[int]] = [[] for _ in range(self.n_clauses)]

        self._init_data_structures()

    def _init_data_structures(self) -> None:
        """
        Build the frequency, occurrence, and watcher data structures for each clause.
        Tautological clauses are marked as inactive.
        """
        for cid, clause in enumerate(self.clauses):
            # Mark clause as inactive if it is tautological.
            if any(-lit in clause for lit in clause):
                self.active_clauses[cid] = False
                continue

            # Update frequency counts and occurrences for each literal in the clause.
            for lit in clause:
                if lit > 0:
                    self.pos_frequency[lit] += 1
                    self.pos_occurrences[lit].append(cid)
                else:
                    self.neg_frequency[-lit] += 1
                    self.neg_occurrences[-lit].append(cid)

            # Initialize watchers: choose the first two literals (or one if unit clause).
            clause_list = list(clause)
            if len(clause_list) >= 2:
                self.watchers[cid] = [clause_list[0], clause_list[1]]
            elif len(clause_list) == 1:
                self.watchers[cid] = [clause_list[0]]

    def is_empty(self) -> bool:
        """
        Returns True if no active clauses remain (i.e., the formula is satisfied).
        """
        return not any(self.active_clauses)

    def has_empty_clause(self) -> bool:
        """
        Returns True if there is any active clause that is empty, indicating unsatisfiability.
        """
        for cid, active in enumerate(self.active_clauses):
            if active and len(self.clauses[cid]) == 0:
                return True
        return False

    def pure_literals(self) -> List[Literal]:
        """
        Compute and return all pure literals from active clauses.

        A literal is pure if it appears in the formula in only one polarity.
        """
        result: List[Literal] = []
        for var in range(1, self.n_vars + 1):
            if self.pos_frequency[var] > 0 and self.neg_frequency[var] == 0:
                result.append(var)
            elif self.neg_frequency[var] > 0 and self.pos_frequency[var] == 0:
                result.append(-var)
        return result

    def pick_branch_literal(self) -> int:
        """
        Choose a branching literal using a heuristic based on frequency.

        The heuristic
          - Considers only variables that appear in both polarities.
          - Chooses the variable with the highest total frequency (sum of positive and negative).
          - Returns the polarity (positive or negative) with the higher individual frequency.

        Returns:
          - A literal (int) to branch on, or 0 if no candidate is found.
        """
        heap = []
        for var in range(1, self.n_vars + 1):
            if self.pos_frequency[var] > 0 and self.neg_frequency[var] > 0:
                total = self.pos_frequency[var] + self.neg_frequency[var]
                heapq.heappush(heap, (-total, var))  # negative total to simulate a max-heap
        if not heap:
            return 0  # No candidate found

        _, var = heapq.heappop(heap)
        return var if self.pos_frequency[var] >= self.neg_frequency[var] else -var

    def assign_literal(self, lit: int) -> List[Literal]:
        """
        Assign a literal as True and propagate its effects.

        This method:
          1. Deactivates all clauses that are satisfied by the literal.
          2. Removes occurrences of the opposite literal (-lit) from all active clauses,
             updating frequencies, occurrence lists, and watchers.
          3. Collects any clauses that become unit as a result.

        Parameters:
          - lit: The literal to assign as True.

        Returns:
          - A list of unit literals (each a Literal) newly produced by this assignment.
        """
        newly_units: List[Literal] = []

        # 1. Deactivate clauses containing lit.
        affected_clauses = self.pos_occurrences[lit][:] if lit > 0 else self.neg_occurrences[-lit][:]
        for cid in affected_clauses:
            if self.active_clauses[cid]:
                self.active_clauses[cid] = False
                # Update frequencies and remove clause id from occurrence lists for all literals in the clause.
                for l in self.clauses[cid]:
                    self.update_freq_occ(cid, l)
                # Clear watchers for an inactive clause.
                self.watchers[cid] = []

        # 2. Remove occurrences of -lit from active clauses.
        neg_lit: Literal = -lit
        affected_clauses = self.pos_occurrences[neg_lit][:] if neg_lit > 0 else self.neg_occurrences[-neg_lit][:]
        for cid in affected_clauses:
            # Ignore inactive clauses and clauses that do not contain neg_lit.
            if not self.active_clauses[cid]:
                continue
            clause = self.clauses[cid]
            if not neg_lit in clause:
                continue
            clause.discard(neg_lit)             # Remove neg_lit from the clause.
            self.update_freq_occ(cid, neg_lit)  # Update frequencies and occurrence lists.

            # 3. Update watchers for this clause if neg_lit was one of them.
            if neg_lit in self.watchers[cid]:
                # Build a set of currently watched literals for fast lookup.
                current_watches = set(self.watchers[cid])
                new_watch: Literal | None = None
                for candidate in clause:
                    if candidate not in current_watches:
                        new_watch = candidate
                        break
                if new_watch is not None:
                    # Replace the watched literal neg_lit with new_watch.
                    idx = self.watchers[cid].index(neg_lit)
                    self.watchers[cid][idx] = new_watch
                else:
                    # No candidate found: update watchers to reflect the current clause.
                    self.watchers[cid] = list(clause)

            # 4. Check if clause has become unit and record its sole literal.
            if self.active_clauses[cid] and len(clause) == 1:
                only_lit = next(iter(clause))
                newly_units.append(only_lit)

        return newly_units

    def update_freq_occ(self, cid, lit):
        """
        The method decrements the frequency counts for lit and removes cid from the occurrence list of lit.
        """
        if lit > 0:
            self.pos_frequency[lit] = max(0, self.pos_frequency[lit] - 1)
            if cid in self.pos_occurrences[lit]:
                self.pos_occurrences[lit].remove(cid)
        else:
            self.neg_frequency[-lit] = max(0, self.neg_frequency[-lit] - 1)
            if cid in self.neg_occurrences[-lit]:
                self.neg_occurrences[-lit].remove(cid)

class DPLLSolver:
    """
    Implements the DPLL algorithm with in-place updates using frequency arrays,
    occurrence lists, and two-watched literal scheme for unit propagation.
    """

    def __init__(self, formula: Formula, logger=None):
        """
        Initialize the solver with a formula and an optional logger.

        Parameters:
          - formula: The Formula object representing the CNF.
          - logger: Optional logger for debug/info messages.
        """
        self.formula = formula
        self.logger = logger

    def solve_dpll(self, counter: Counter) -> bool:
        """
        Solve the formula using DPLL.

        This method recursively applies unit propagation, pure literal elimination,
        and branching. It uses an external Counter (a mutable counter object)
        to track the number of recursive calls.

        Parameters:
          - counter: A Counter instance used to count recursive calls.

        Returns:
          - True if the formula is satisfiable; False otherwise.
        """
        counter.increment()
        if self.formula.has_empty_clause():
            return False
        if self.formula.is_empty():
            return True

        # 1. Unit propagation: assign all unit clauses repeatedly.
        if not self.unit_propagation():
            return False
        if self.formula.is_empty():
            return True

        # 2. Pure literal elimination: assign pure literals until no more are found.
        changed = True
        while changed:
            changed = False
            pures = self.formula.pure_literals()
            if pures:
                changed = True
                for p in pures:
                    if not self.assign_lit(p):  # Conflict encountered.
                        return False
                if self.formula.is_empty():
                    return True

        if self.formula.has_empty_clause():
            return False
        if self.formula.is_empty():
            return True

        # 3. Branching: choose a literal using the heuristic.
        chosen_lit = self.formula.pick_branch_literal()
        if chosen_lit == 0:
            return True  # No literal left implies a complete assignment.

        # Branch 1: Assume chosen_lit is True.
        saved_state = self._save_state()
        if self.assign_lit(chosen_lit):
            if self.solve_dpll(counter):
                return True
        self._restore_state(saved_state)

        # Branch 2: Assume chosen_lit is False.
        saved_state = self._save_state()
        if self.assign_lit(-chosen_lit):
            if self.solve_dpll(counter):
                return True
        self._restore_state(saved_state)

        return False

    def unit_propagation(self) -> bool:
        """
        Repeatedly applies unit propagation until no unit clauses remain.

        Returns:
          - False if a conflict (empty clause) is encountered.
          - True otherwise.
        """
        changed = True
        while changed:
            changed = False
            for cid, active in enumerate(self.formula.active_clauses):
                if not active:
                    continue
                clause = self.formula.clauses[cid]
                if len(clause) == 0:
                    return False
                if len(clause) == 1:
                    unit_lit = next(iter(clause))
                    if not self.assign_lit(unit_lit):
                        return False
                    changed = True
                    break  # Restart scanning after an assignment.
        return True

    def assign_lit(self, lit: int) -> bool:
        """
        Assigns a literal as True, propagates unit clauses, and checks for conflicts.

        Parameters:
          - lit: The literal to assign.

        Returns:
          - True if assignment and propagation succeed.
          - False if a conflict is encountered.
        """
        new_units = self.formula.assign_literal(lit)
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
        Creates a snapshot of the current formula state.

        Note: In production solvers, an incremental undo stack is more efficient. It would be a next step.

        Returns:
          A tuple containing deep copies of the formula’s state components.
        """
        active_copy = list(self.formula.active_clauses)
        clause_copy = [set(cl) for cl in self.formula.clauses]
        pos_occ_copy = [list(lst) for lst in self.formula.pos_occurrences]
        neg_occ_copy = [list(lst) for lst in self.formula.neg_occurrences]
        pos_freq_copy = self.formula.pos_frequency[:]
        neg_freq_copy = self.formula.neg_frequency[:]
        watch_copy = [list(w) for w in self.formula.watchers]
        return active_copy, clause_copy, pos_occ_copy, neg_occ_copy, pos_freq_copy, neg_freq_copy, watch_copy

    def _restore_state(self, saved) -> None:
        """
        Restores the formula state from a snapshot.

        Parameters:
          - saved: The snapshot tuple created by _save_state().
        """
        (active_copy, clause_copy, pos_occ_copy, neg_occ_copy, pos_freq_copy, neg_freq_copy, watch_copy) = saved
        self.formula.active_clauses = active_copy
        self.formula.clauses = clause_copy
        self.formula.pos_occurrences = pos_occ_copy
        self.formula.neg_occurrences = neg_occ_copy
        self.formula.pos_frequency = pos_freq_copy
        self.formula.neg_frequency = neg_freq_copy
        self.formula.watchers = watch_copy


def dpll(clauses: Set[frozenset], counter: Counter, logger=None, n_vars: int = 0) -> bool:
    """
    External interface for the DPLL algorithm.

    Converts a set of frozensets (each representing a clause) into a mutable formula,
    instantiates the DPLL solver, and returns the satisfiability result.

    Parameters:
      - clauses: A set of frozensets, where each frozenset is a clause.
      - counter: A Counter instance for counting recursive calls.
      - logger: Optional logger for debug information.
      - n_vars: The number of variables in the formula.

    Returns:
      - True if the formula is satisfiable, False otherwise.
    """
    # Convert set[frozenset] => list[set[int]] for in-place manipulations.
    list_of_clauses: CNF = []
    for clause in clauses:
        list_of_clauses.append(set(clause))

    formula = Formula(list_of_clauses, n_vars)
    solver = DPLLSolver(formula, logger=logger)
    result = solver.solve_dpll(counter)
    return result
