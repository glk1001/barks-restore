import logging
import subprocess
from typing import List


def run_gmic(params: List[str]) -> None:
    gmic_path = "gmic"
    run_args = [gmic_path, "-v", "+1"]
    run_args.extend(params)

    logging.debug(f"Running gmic: {' '.join(run_args)}.")

    process = subprocess.Popen(run_args, stdout=subprocess.PIPE, text=True)

    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            logging.info(output.strip())

    rc = process.poll()
    if rc != 0:
        raise Exception("Gmic failed.")
