import argparse
import cProfile
import io
import logging
import pstats
from glob import glob

from dp_baseline import dp_default
from dpll import dp, dpll, classical_dpll
from dpll_watchers import dpll as dpll_watchers
from utils import run_dp_on_files


class Algorithms:
    DP_DEFAULT = dp_default
    DP = dp
    DPLL = dpll
    CLASSICAL_DPLL = classical_dpll
    DPLL_WATCHERS = dpll_watchers

    str_to_algorithm = {
        'dp_default': DP_DEFAULT,
        'dp': DP,
        'dpll': DPLL,
        'classical_dpll': CLASSICAL_DPLL,
        'dpll_watchers': DPLL_WATCHERS
    }


def main():
    # Folder names for SAT and NON-SAT problems
    sat_folder = 'uf50/*.cnf'
    non_sat_folder = 'uuf50/*.cnf'

    # Example usage with multiple CNF files
    cnf_files = glob(sat_folder)
    cnf_files += glob(non_sat_folder)

    cnf_files = sorted(cnf_files)

    if RUN_ON_LARGE_CNF:
        cnf_files += 'uf175-01.cnf', 'uuf150-01.cnf'
    if RUN_ON_LARGE_CNF_ONLY:
        cnf_files = 'uf175-01.cnf', 'uuf150-01.cnf'
    if FILE_NAME:
        cnf_files = [FILE_NAME]

    time_taken = run_dp_on_files(cnf_files, algorithm=ALG, logger=logger, num_runs=NUM_RUNS)

    logger.info(f'Total time taken: {time_taken:.5f} seconds for {len(cnf_files)} files, with {NUM_RUNS} run(s) each.')


if __name__ == '__main__':
    # Parse arguments to get the algorithm name, whether to profile the code, and whether to run on large CNF files
    parser = argparse.ArgumentParser()
    parser.add_argument('--algorithm', type=str, default='dpll_watchers',
                        help='The algorithm to use for solving the SAT problem.')
    parser.add_argument('--file_name', type=str, default='',
                        help='The cnf file to test the algorithm on.')
    parser.add_argument('--profile', type=bool, default=False,
                        help='Whether to profile the code.')
    parser.add_argument('--run_on_large_cnf', type=bool, default=False,
                        help='Whether to run the algorithm on large problems.')
    parser.add_argument('--run_on_large_cnf_only', type=bool, default=False,
                        help='Whether to run the algorithm on large problems only.')
    parser.add_argument('--num_runs', type=int, default=1,
                        help='The number of times to run the algorithm.')
    parser.add_argument('--log_level', type=str, default='INFO',
                        help='The logging level to use.')
    args = parser.parse_args()
    NUM_RUNS = args.num_runs
    ALG = Algorithms.str_to_algorithm[args.algorithm]
    FILE_NAME = args.file_name if args.file_name else None
    PROFILE = args.profile
    LOG_LEVEL = args.log_level
    RUN_ON_LARGE_CNF = args.run_on_large_cnf
    RUN_ON_LARGE_CNF_ONLY = args.run_on_large_cnf_only

    profiler = cProfile.Profile()

    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if PROFILE:
        profiler.enable()
    main()
    if PROFILE:
        profiler.disable()

        # Create a stream to capture the profiling data
        s = io.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
        ps.print_stats()

        # Output the profiling results to a file
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        name = f"results/{ALG.__name__}_{date}_profile.txt"
        with open(name, 'w') as f:
            f.write(s.getvalue())

        print(s.getvalue())