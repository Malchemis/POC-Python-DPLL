from glob import glob
from utils import run_dp_on_files
from DavisPutnamDefaultCleaned import dp as dp_default
from dp import dp, dpll, classical_dpll
from dp_with_watchers import dpll as dpll_watchers
import logging

# To profile (optional)
import cProfile
import pstats
import io


class Algorithms:
    DP_DEFAULT = dp_default
    DP = dp
    DPLL = dpll
    DPLL_WATCHERS = dpll_watchers
    CLASSICAL_DPLL = classical_dpll


def main():
    # Folder names for SAT and NON-SAT problems
    sat_folder = 'uf50/*.cnf'
    non_sat_folder = 'uuf50/*.cnf'

    # Example usage with multiple CNF files
    cnf_files = glob(sat_folder)
    cnf_files += glob(non_sat_folder)

    cnf_files = sorted(cnf_files)

    if large_problems:
        cnf_files += 'uf175-01.cnf', 'uuf150-01.cnf'

    time_taken = run_dp_on_files(cnf_files, algorithm=Algorithms.DPLL_WATCHERS, logger=logger)

    logger.info(f'Total time taken: {time_taken:.3f} seconds')


if __name__ == '__main__':
    # Set to True to enable profiling
    PROFILE = False
    # Set to True to run on large problems (uf175-01.cnf, uuf150-01.cnf which are very time-consuming)
    large_problems = True

    profiler = cProfile.Profile()

    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create a profiler
    if PROFILE:
        profiler.enable()

    counter = 0
    main()

    if PROFILE:
        profiler.disable()

        # Create a stream to capture the profiling data
        s = io.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
        ps.print_stats()

        # Output the profiling results to a file
        with open("results/profiling_results_dp_optimized_with_lrucache.txt", "w") as f:
            f.write(s.getvalue())

        print(s.getvalue())