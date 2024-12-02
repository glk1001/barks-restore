import argparse
import logging
import os
import sys
import time
from typing import List

from intspan import intspan

from barks_fantagraphics.comic_book import get_barks_path
from barks_fantagraphics.comics_database import (
    ComicsDatabase,
    PageType,
    get_default_comics_database_dir,
)
from src.upscale_image import upscale_image_file


def setup_logging(log_level) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=log_level,
    )


RESTORABLE_PAGE_TYPES = [
    PageType.BODY,
    PageType.FRONT_MATTER,
    PageType.BACK_MATTER,
]

COMICS_DATABASE_DIR_ARG = "--comics-database-dir"
VOLUME_ARG = "--volume"
TITLE_ARG = "--title"

SCALE = 4


def get_args():
    parser = argparse.ArgumentParser(
        description="Upscayl jpg images in specified Fantagraphics volumes."
    )

    parser.add_argument(
        COMICS_DATABASE_DIR_ARG,
        action="store",
        type=str,
        default=get_default_comics_database_dir(),
    )
    parser.add_argument(
        VOLUME_ARG,
        action="store",
        type=str,
        required=False,
    )
    parser.add_argument(
        TITLE_ARG,
        action="store",
        type=str,
        required=False,
    )

    args = parser.parse_args()

    return args


def upscayl(title_list: List[str]) -> None:
    start = time.time()

    num_upscayled_files = 0
    for title in title_list:
        logging.info(f'Upscayling story "{title}"...')

        comic = comics_database.get_comic_book(title)

        srce_files = comic.get_srce_with_fixes_story_files(RESTORABLE_PAGE_TYPES)
        upscayl_files = comic.get_srce_upscayled_story_files(RESTORABLE_PAGE_TYPES)

        for srce_file, upscayl_file in zip(srce_files, upscayl_files):
            if not os.path.isfile(srce_file[0]):
                raise Exception(f'Could not find srce file: "{srce_file[0]}".')
            if os.path.isfile(upscayl_file):
                logging.warning(
                    f'Dest upscayl file exists - skipping: "{get_barks_path(upscayl_file)}".'
                )
                continue

            # print(f'Upscayling srce file "{srce_file[0]}" to dest upscayl "{upscayl_file}".')
            upscale_image_file(srce_file[0], upscayl_file, SCALE)

            num_upscayled_files += 1

    logging.info(
        f"\nTime taken to upscayl all {num_upscayled_files} files: {int(time.time() - start)}s."
    )


setup_logging(logging.INFO)

cmd_args = get_args()
comics_database = ComicsDatabase(cmd_args.comics_database_dir)

if cmd_args.volume and cmd_args.title:
    print(f"ERROR: You can only have one of '{VOLUME_ARG}' or '{TITLE_ARG}'.")
    sys.exit(1)

if cmd_args.title:
    titles = [cmd_args.title]
elif cmd_args.volume:
    vol_list = list(intspan(cmd_args.volume))
    titles = comics_database.get_all_story_titles_in_fantagraphics_volume(vol_list)
else:
    print(f"ERROR: You must specify one of '{VOLUME_ARG}' or '{TITLE_ARG}'.")
    sys.exit(1)

upscayl(titles)
