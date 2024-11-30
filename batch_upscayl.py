import argparse
import os

from intspan import intspan

from barks_fantagraphics.comics_database import (
    ComicsDatabase,
    PageType,
    get_default_comics_database_dir,
)
from barks_fantagraphics.comics_info import JPG_FILE_EXT, PNG_FILE_EXT
from barks_fantagraphics.comics_utils import get_story_files_of_page_type
from experiments.upscale_image import upscale_image_file

RESTORABLE_PAGE_TYPES = [
    PageType.BODY,
    PageType.FRONT_MATTER,
    PageType.BACK_MATTER,
]

COMICS_DATABASE_DIR_ARG = "--comics-database-dir"
VOLUME_ARG = "--volume"

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
        required=True,
    )

    args = parser.parse_args()

    return args


def upscale(in_file: str, out_file: str) -> None:
    if not os.path.isfile(in_file):
        raise Exception(f'Could not find srce file: "{in_file}".')
    if os.path.isfile(out_file):
        print(f'Dest file exists - skipping: "{out_file}".')
        return

    print(f'Upscayling srce file "{in_file}" to dest "{out_file}".')
    upscale_image_file(in_file, out_file, SCALE)


cmd_args = get_args()
comics_database = ComicsDatabase(cmd_args.comics_database_dir)
vol_list = list(intspan(cmd_args.volume))

titles = comics_database.get_all_story_titles_in_fantagraphics_volume(vol_list)

srce_file_list = []
dest_file_list = []
for title in titles:
    comic_book = comics_database.get_comic_book(title)

    srce_dir = comic_book.get_srce_image_dir()
    srce_files = get_story_files_of_page_type(
        srce_dir, comic_book, JPG_FILE_EXT, RESTORABLE_PAGE_TYPES
    )
    srce_file_list.extend(srce_files)

    dest_dir = comic_book.get_srce_upscayled_image_dir()
    dest_files = get_story_files_of_page_type(
        dest_dir, comic_book, PNG_FILE_EXT, RESTORABLE_PAGE_TYPES
    )
    dest_file_list.extend(dest_files)

for srce_file, dest_file in zip(srce_file_list, dest_file_list):
    upscale(srce_file, dest_file)
