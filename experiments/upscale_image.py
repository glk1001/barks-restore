import os
import subprocess
from pathlib import Path

from PIL.features import check


def upscale_image_file(in_file: str, out_file: str, scale: int = 2):
    upscayl_bin = os.path.join(str(Path.home()), ".local/share/upscayl/bin/upscayl-bin")
    upscayl_models_dir = os.path.join(str(Path.home()), ".local/share/upscayl/models")

    run_args = [
        upscayl_bin,
        "-i",
        in_file,
        "-o",
        out_file,
        "-s",
        str(scale),
        "-n",
        "ultramix_balanced",
        "-f",
        "jpg",
        "-c",
        '0',
        "-m",
        upscayl_models_dir,
    ]

    # subprocess.run(
    #     run_args,
    #     capture_output=True,
    #     text=True,
    #     check=True,
    # )
    #

    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, text=True)

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())

    rc = process.poll()
    if rc != 0:
        raise Exception("Upscayl failed.")
