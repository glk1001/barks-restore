import os
from typing import List, Dict

import cv2 as cv
from PIL import Image
from PIL.PngImagePlugin import PngInfo

PNG_PROPERTY_GROUP = "BARKS"
SAVE_JPG_QUALITY = 95
SAVE_JPG_COMPRESS_LEVEL = 9


def write_cv_image_file(
    file: str, image: cv.typing.MatLike, comments: List[str] = None
):
    if os.path.splitext(file)[1] == ".jpg":
        _write_cv_jpeg_file(file, image, comments)
        return

    if os.path.splitext(file)[1] == ".png":
        _write_cv_png_file(file, image, comments)
        return

    cv.imwrite(file, image)


def add_png_metadata(png_file: str, metadata: Dict[str, str]):
    pil_image = Image.open(png_file, "r")

    png_metadata = PngInfo()
    for key in metadata:
        png_metadata.add_text(f"{PNG_PROPERTY_GROUP}:{key}", metadata[key])

    pil_image.save(png_file, pnginfo=png_metadata)


def _write_cv_png_file(file: str, image: cv.typing.MatLike, comments: List[str]):
    color_converted = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_converted)

    metadata = PngInfo()
    comments_str = "" if comments is None else "\n".join(comments)
    metadata.add_text(f"{PNG_PROPERTY_GROUP}:Comments", comments_str)

    pil_image.save(file, pnginfo=metadata)


def _write_cv_jpeg_file(file: str, image: cv.typing.MatLike, comments: List[str]):
    comments_str = "" if comments is None else "\n".join(comments)
    color_converted = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_converted)
    pil_image.save(
        file,
        optimize=True,
        compress_level=SAVE_JPG_COMPRESS_LEVEL,
        quality=SAVE_JPG_QUALITY,
        comment=comments_str,
    )
