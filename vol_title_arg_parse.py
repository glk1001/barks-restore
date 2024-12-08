import argparse

from barks_fantagraphics.comics_database import get_default_comics_database_dir

COMICS_DATABASE_DIR_ARG = "--comics-database-dir"
VOLUME_ARG = "--volume"
TITLE_ARG = "--title"


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

    if not _validate(args):
        return None

    return args


def _validate(args) -> bool:
    if args.volume and args.title:
        print(f"ERROR: You can only have one of '{VOLUME_ARG}' or '{TITLE_ARG}'.")
        return False
    if args.volume is None and args.title is None:
        print(f"ERROR: You must specify one of '{VOLUME_ARG}' or '{TITLE_ARG}'.")
        return False

    return True
