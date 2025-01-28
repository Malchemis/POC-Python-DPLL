from glob import glob
from utils import run_dp_on_files
from dp import dp, dpll
import logging

# To profile (optional)
import cProfile
import pstats
import io


def main():
    # Folder names for SAT and NON-SAT problems
    sat_folder = 'uf50'
    non_sat_folder = 'uuf50'

    # Example usage with multiple CNF files
    cnf_files = glob(f'{sat_folder}/*.cnf')
    cnf_files += glob(f'{non_sat_folder}/*.cnf')

    if large_problems:
        cnf_files += 'uf175-01.cnf', 'uuf150-01.cnf'

    cnf_files = sorted(cnf_files)

    time_taken = run_dp_on_files(cnf_files, algorithm=dpll, logger=logger)

    logger.info(f'Total time taken: {time_taken:.3f} seconds')


if __name__ == '__main__':
    # Set to True to enable profiling
    PROFILE = False
    # Set to True to run on large problems (uf175-01.cnf, uuf150-01.cnf which are very time-consuming)
    large_problems = False

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