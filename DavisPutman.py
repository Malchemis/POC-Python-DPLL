from numpy import zeros, array


# return True if the list of integers contains an integer and its opposite
# ex.is_tautologie([1,2,3,-1,5]) return True 
def is_tautologie(clause: list) -> bool:
    for i in clause:
        op_i = -i
        if op_i in clause:
            return True
    return False


def regle_1(clauses: list) -> list:
    """Règle 1 : oter tautologie -> clause contenant l et non l"""
    l2 = []
    for c in clauses:
        if not is_tautologie(c):
            l2.append(c)
    if verbose:
        if not clauses == l2:
            print("règle 1 activée")
    return l2


l1 = [[1, 2], [1, 4, -1], [8, 1, 6, 4, 9, 1, -6], [-2, 4], [1]]


################################################

def ote_val_from_clauses(clauses: list, value: int) -> list:
    liste2 = []
    for c in clauses:
        c2 = [i for i in c if i != value]
        liste2.append(c2)
    return liste2


def ote_clauses_with_val(clauses: list, value: int) -> list:
    liste2 = []
    for c in clauses:
        if not value in c:
            liste2.append(c)
    return liste2


def regle_2(clauses: list) -> list:
    """Règle 2 : clause contient 1 seul littéral -> enlever les clauses le contenant, et enlever l'apparition de son inverse ailleurs"""
    for c in clauses:
        if len(c) == 1:
            value = c[0]
            clauses2 = ote_clauses_with_val(clauses, value)
            clauses3 = ote_val_from_clauses(clauses2, -value)
            if verbose: print("regle 2 activee, retrait de ", value)
            return clauses3
    return clauses


l2 = [[1], [1, 2], [1, 6, 4], [-2, 4], [-1, 7]]


################################################

def exist_in_clauses(value: int, clauses: list) -> bool:
    """retourne vrai si la valeur value existe dans au moins une clause"""
    for c in clauses:
        if value in c: return True
    return False


def single_lit(clauses: list) -> int:
    """retourne un literal qui apparait dans des clauses mais dont l'opposé n'apparait jamais"""
    for c in clauses:
        for i in c:
            if not exist_in_clauses(-i, clauses): return i
    return 0


def regle_3(clauses: list) -> list:
    """Règle 3 : 1 littéral apparaît dans des clauses, son inverse n'apparait jamais -> enlever les clauses le contenant"""
    lit = single_lit(clauses)
    if lit != 0:
        clauses2 = ote_clauses_with_val(clauses, lit)
        if verbose: print("regle 3 activee, retrait de ", lit)
        return clauses2
    return clauses


l3 = [[1, 2], [1, 6, 4], [-2, 4]]


################################################

def bigger_clauses(clauses: list) -> list:
    """retourne les clauses qui contiennent d'autres clauses"""
    clauses2 = []
    for c in clauses:
        for c2 in clauses:
            if c != c2:
                if all(elem in c for elem in c2):
                    clauses2.append(c)
    return clauses2


def regle_4(clauses: list) -> list:
    """Règle 4 : si une  clause est contenu dans d'autres -> enlever les autres"""
    clauses2 = bigger_clauses(clauses)
    clauses3 = [c for c in clauses if c not in clauses2]
    if verbose:
        if clauses2 != []: print("regle 4 activee, retrait des clause qui contiennent ", clauses2)
    return clauses3


l4 = [[1, 2], [1, 6, 4], [1, 2, 4], [1, 6]]


################################################

def get_not_single(clauses: list) -> int:
    """retourne un littéral l dont son inverse apparaît également """
    for c in clauses:
        for i in c:
            if exist_in_clauses(-i, clauses): return i


def regle_5(clauses: list) -> list:
    """Règle 5 : Créer des mondes -> choisir un littéral l dont son inverse apparaît également 
    -> créer 2 formules,
    - F1) contenant les clauses de F sauf celles contenant l
         et où les apparitions de ¬l sont ôtées
    - F2) contenant les clauses de F sauf celles contenant ¬l
      et où les apparitions de l sont ôtées
    """
    l = get_not_single(clauses)
    if l != 0:
        clauses21 = ote_clauses_with_val(clauses, l)
        clauses31 = ote_val_from_clauses(clauses21, -l)
        clauses22 = ote_clauses_with_val(clauses, -l)
        clauses32 = ote_val_from_clauses(clauses22, l)
        if verbose: print("regle 5 activee, creation de deux mondes à partir de ", l, " et de ", -l)
        return (clauses31, clauses32)


l5 = [[1, 2], [1, 6, 4], [-1, 2, 4], [5, 6], [4, 5, -1]]


################################################

def formules_egales(f1: list, f2: list) -> bool:
    """retourne vrai si les formules f1 et f2 sont identiques"""
    ##TODO: utiliser des sorted set pour une "vraie" comparaison
    if len(f1) != len(f2): return False
    for c in f1:
        if c not in f2: return False
    return True


cpt = 0
verbose = False


def DP(clauses: list) -> bool:
    """retourne vrai si le DPLL est fini"""
    global cpt
    cpt += 1
    print("résolution de ", clauses) if verbose else None
    clr1 = regle_1(clauses)
    if len(clr1) == 0:
        print("succes") if verbose else None
        return True
    if [] in clr1:
        print("echec") if verbose else None
        return False
    clr2 = regle_2(clr1)
    if len(clr2) == 0:
        print("succes") if verbose else None
        return True
    if [] in clr2:
        print("echec") if verbose else None
        return False
    if not formules_egales(clr1, clr2): return DP(clr2)
    clr3 = regle_3(clr2)
    if len(clr3) == 0:
        print("succes") if verbose else None
        return True
    if [] in clr3:
        print("echec") if verbose else None
        return False
    if not formules_egales(clr2, clr3): return DP(clr3)
    clr4 = regle_4(clr3)
    if len(clr4) == 0:
        print("succes") if verbose else None
        return True
    if [] in clr4:
        print("echec") if verbose else None
        return False
    if not formules_egales(clr3, clr4): return DP(clr4)
    clr51, clr52 = regle_5(clr4)
    mondes_unis = DP(clr51) or DP(clr52)
    print("fin résolution de ", clauses) if verbose else None
    return mondes_unis


def lire_cnf(fichier):
    """
    Lit un fichier CNF en format DIMACS et retourne une liste de listes représentant les clauses.

    :param fichier: Le chemin du fichier CNF à lire.
    :return: Une liste de listes où chaque sous-liste représente une clause.
    """
    clauses = []

    with open(fichier, 'r') as f:
        for ligne in f:
            if ligne.startswith("%"): break
            # Ignorer les lignes de commentaires et le préambule
            if ligne.startswith('c') or ligne.startswith('p'):
                continue

            # Diviser la ligne en entiers
            literals = list(map(int, ligne.split()))

            # Retirer le 0 de fin de clause
            if literals[-1] == 0:
                literals.pop()

            # Ajouter la clause à la liste des clauses
            if literals:
                clauses.append(literals)

    return clauses


## d'une format liste de listes vers un fomat DIMACS
def liste_vers_DIMACS(clauses):
    nb_clauses = len(clauses)
    maxi = clauses[0][0]
    mini = clauses[0][0]
    texte = ""
    for c in clauses:
        localmax = max(c)
        localmin = min(c)
        if localmax > maxi: maxi = localmax
        if localmin < mini: mini = localmin
        for var in c:
            texte = texte + str(var) + " "
        texte = texte + "0\n"

    nb_vars = max(maxi, abs(mini))
    texte = f"p cnf {nb_vars} {nb_clauses}\n" + texte
    print(texte)


def main():
    # We will use the Davis-Putnam algorithm to solve the following problems :
    # The first 2 are only for testing (simple cases)
    first_file = "uf50/uf50-01.cnf"
    second_file = "uuf50/uuf50-01.cnf"
    # The last 2 are for the final test (but very long on normal dp)
    # third_file = "uf175-01.cnf"
    # fourth_file = "uuf150-01.cnf"

    # Reading the CNF files
    first_clauses = lire_cnf(first_file)
    second_clauses = lire_cnf(second_file)
    # third_clauses = lire_cnf(third_file)
    # fourth_clauses = lire_cnf(fourth_file)

    # Testing the Davis-Putnam algorithm
    import cProfile
    import pstats
    import io
    from time import time
    global verbose
    global cpt

    profiler = cProfile.Profile()
    profiler.enable()

    verbose = False
    cpt = 0
    start = time()
    print(DP(first_clauses))
    print("Time : ", time() - start, "for file ", first_file, "with ", cpt, "calls")
    cpt = 0
    start = time()
    print(DP(second_clauses))
    print("Time : ", time() - start, "for file ", second_file, "with ", cpt, "calls")

    profiler.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


if __name__ == "__main__":
    main()