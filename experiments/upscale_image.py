import logging
import os
import subprocess
from pathlib import Path

from image_io import add_png_metadata

UPSCAYL_BIN = os.path.join(str(Path.home()), ".local/share/upscayl/bin/upscayl-bin")
UPSCAYL_MODELS_DIR = os.path.join(str(Path.home()), ".local/share/upscayl/models")
UPSCAYL_MODEL = "ultramix_balanced"
UPSCAYL_OUTPUT_FORMAT = "png"
UPSCAYL_OUTPUT_EXTENSION = ".png"


def upscale_image_file(in_file: str, out_file: str, scale: int = 2):
    assert os.path.splitext(out_file)[1] == UPSCAYL_OUTPUT_EXTENSION

    run_args = [
        UPSCAYL_BIN,
        "-i",
        in_file,
        "-o",
        out_file,
        "-s",
        str(scale),
        "-n",
        UPSCAYL_MODEL,
        "-f",
        UPSCAYL_OUTPUT_FORMAT,
        "-c",
        "0",
        "-m",
        UPSCAYL_MODELS_DIR,
        "-v",
    ]

    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, text=True)

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            logging.info(output.strip())

    rc = process.poll()
    if rc != 0:
        raise Exception("Upscayl failed.")

    metadata = {
        "Source file": in_file,
        "Scale": str(scale),
        "Upscayl model": UPSCAYL_MODEL,
    }
    add_png_metadata(out_file, metadata)
