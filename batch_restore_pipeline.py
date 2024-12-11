import concurrent.futures
import logging
import os
import sys
import time
from pathlib import Path
from typing import List

import psutil

from barks_fantagraphics.comics_cmd_args import CmdArgs, CmdArgNames
from barks_fantagraphics.comics_consts import RESTORABLE_PAGE_TYPES
from barks_fantagraphics.comics_utils import get_relpath, setup_logging
from src.restore_pipeline import RestorePipeline, check_for_errors

SCALE = 4
SMALL_RAM = 16 * 1024 * 1024 * 1024


def restore(title_list: List[str]) -> None:
    start = time.time()

    restore_processes = []
    for title in title_list:
        logging.info(f'Processing story "{title}".')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_final_srce_story_files(RESTORABLE_PAGE_TYPES)
        upscayl_files = comic.get_final_srce_upscayled_story_files(RESTORABLE_PAGE_TYPES)
        dest_restored_files = comic.get_srce_restored_story_files(RESTORABLE_PAGE_TYPES)
        dest_restored_upscayled_files = comic.get_srce_restored_upscayled_story_files(
            RESTORABLE_PAGE_TYPES
        )
        dest_restored_svg_files = comic.get_srce_restored_svg_story_files(RESTORABLE_PAGE_TYPES)

        for (
            srce_file,
            upscayl_file,
            dest_restored_file,
            dest_upscayled_restored_file,
            dest_svg_restored_file,
        ) in zip(
            srce_files,
            upscayl_files,
            dest_restored_files,
            dest_restored_upscayled_files,
            dest_restored_svg_files,
        ):
            if not os.path.isfile(srce_file[0]):
                raise Exception(f'Could not find srce file: "{srce_file[0]}".')
            if not os.path.isfile(upscayl_file[0]):
                raise Exception(f'Could not find srce upscayl file: "{upscayl_file[0]}".')
            if os.path.isfile(dest_restored_file):
                logging.warning(
                    f'Dest file exists - skipping: "{get_relpath(dest_restored_file)}".'
                )
                continue

            # print(f'Restoring srce file "{srce_file}", "{upscayl_file}" to dest "{dest_restored_file}".')

            restore_processes.append(
                RestorePipeline(
                    work_dir,
                    Path(srce_file[0]),
                    Path(upscayl_file[0]),
                    SCALE,
                    Path(dest_restored_file),
                    Path(dest_upscayled_restored_file),
                    Path(dest_svg_restored_file),
                )
            )

    run_restore(restore_processes)

    logging.info(
        f'\nTime taken to restore all {len(restore_processes)} files": {int(time.time() - start)}s.'
    )

    check_for_errors(restore_processes)


part1_max_workers = 10


def run_restore_part1(proc: RestorePipeline):
    logging.info("Starting restore part 1.")
    proc.do_part1()


part2_max_workers = 1 if psutil.virtual_memory().total < SMALL_RAM else 3


def run_restore_part2(proc: RestorePipeline):
    logging.info("Starting restore part 2.")
    proc.do_part2_memory_hungry()


part3_max_workers = 10


def run_restore_part3(proc: RestorePipeline):
    logging.info("Starting restore part 3.")
    proc.do_part3()


part4_max_workers = 1


def run_restore_part4(proc: RestorePipeline):
    logging.info("Starting restore part 4.")
    proc.do_part4_memory_hungry()


def run_restore(restore_processes: List[RestorePipeline]) -> None:
    logging.info(f"Starting restore for {len(restore_processes)} processes.")

    with concurrent.futures.ProcessPoolExecutor(part1_max_workers) as executor:
        for process in restore_processes:
            executor.submit(run_restore_part1, process)

    with concurrent.futures.ProcessPoolExecutor(part2_max_workers) as executor:
        for process in restore_processes:
            executor.submit(run_restore_part2, process)

    with concurrent.futures.ProcessPoolExecutor(part3_max_workers) as executor:
        for process in restore_processes:
            executor.submit(run_restore_part3, process)

    with concurrent.futures.ProcessPoolExecutor(part4_max_workers) as executor:
        for process in restore_processes:
            executor.submit(run_restore_part4, process)


work_dir = os.path.join(f"{Path.home()}/Prj/workdir/restore-tests")
os.makedirs(work_dir, exist_ok=True)

setup_logging(logging.INFO)

cmd_args = CmdArgs("Ocr titles", CmdArgNames.TITLE | CmdArgNames.VOLUME)
args_ok, error_msg = cmd_args.args_are_valid()
if not args_ok:
    logging.error(error_msg)
    sys.exit(1)

comics_database = cmd_args.get_comics_database()

titles = cmd_args.get_titles()

restore(titles)
