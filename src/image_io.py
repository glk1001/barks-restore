import os
from io import BytesIO
from typing import List, Dict

import cairosvg
import cv2 as cv
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from barks_fantagraphics.comics_image_io import (
    METADATA_PROPERTY_GROUP,
    SAVE_PNG_COMPRESSION,
    SAVE_JPG_QUALITY,
    SAVE_JPG_COMPRESS_LEVEL,
    add_png_metadata,
)
from barks_fantagraphics.comics_info import JPG_FILE_EXT, PNG_FILE_EXT
from .gmic_exe import run_gmic

Image.MAX_IMAGE_PIXELS = None


def svg_file_to_png(svg_file: str, png_file: str):
    # background_color = "white"
    background_color = None
    png_image = cairosvg.svg2png(url=svg_file, scale=1, background_color=background_color)

    pil_image = Image.open(BytesIO(png_image))
    pil_image.save(png_file, optimize=True, compress_level=SAVE_PNG_COMPRESSION)


def write_cv_image_file(file: str, image: cv.typing.MatLike, metadata: Dict[str, str] = None):
    if os.path.splitext(file)[1] == JPG_FILE_EXT:
        _write_cv_jpeg_file(file, image, metadata)
        return

    if os.path.splitext(file)[1] == PNG_FILE_EXT:
        _write_cv_png_file(file, image, metadata)
        return

    cv.imwrite(file, image)


def resize_image_file(in_file: str, srce_scale: int, resized_file: str, metadata: Dict[str, str]):
    if os.path.splitext(resized_file)[1] == JPG_FILE_EXT:
        _resize_jpeg_file(in_file, srce_scale, resized_file, metadata)
        return

    if os.path.splitext(resized_file)[1] == PNG_FILE_EXT:
        _resize_png_file(in_file, srce_scale, resized_file, metadata)
        return

    assert False


def _resize_jpeg_file(in_file: str, srce_scale: int, resized_file: str, metadata: Dict[str, str]):
    image = cv.imread(in_file)
    scale = 1.0 / srce_scale
    image = cv.resize(image, (0, 0), fx=scale, fy=scale, interpolation=cv.INTER_AREA)
    write_cv_image_file(resized_file, image, metadata)


def _resize_png_file(in_file: str, srce_scale: int, resized_file: str, metadata: Dict[str, str]):
    assert srce_scale in [2, 4]
    scale_percent = 25 if srce_scale == 4 else 50

    resize_cmd = [
        in_file,
        "+resize[-1]",
        f"{scale_percent}%,{scale_percent}%,1,3,2",
        "output[-1]",
        resized_file,
    ]

    run_gmic(resize_cmd)

    add_png_metadata(resized_file, metadata)


def _write_cv_png_file(file: str, image: cv.typing.MatLike, metadata: Dict[str, str]):
    color_converted = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_converted)

    png_metadata = PngInfo()
    if metadata:
        for key in metadata:
            png_metadata.add_text(f"{METADATA_PROPERTY_GROUP}:{key}", metadata[key])

    pil_image.save(file, pnginfo=png_metadata, optimize=True, compress_level=SAVE_PNG_COMPRESSION)


def _write_cv_jpeg_file(file: str, image: cv.typing.MatLike, metadata: Dict[str, str]):
    comments_str = "" if metadata is None else "\n" + "\n".join(_get_metadata_as_list(metadata))
    color_converted = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_converted)
    pil_image.save(
        file,
        optimize=True,
        compress_level=SAVE_JPG_COMPRESS_LEVEL,
        quality=SAVE_JPG_QUALITY,
        comment=comments_str,
    )


def _get_metadata_as_list(metadata: Dict[str, str]) -> List[str]:
    metadata_list = []

    for key in metadata:
        metadata_list.append(f"{METADATA_PROPERTY_GROUP}:{key}={metadata[key]}")

    return metadata_list
