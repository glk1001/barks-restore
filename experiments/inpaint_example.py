import sys

from inpaint import inpaint_image_file

if __name__ == "__main__":
    input_image_file = sys.argv[1]
    black_ink_remove_file = sys.argv[2]
    black_ink_add_file = sys.argv[3]
    output_inpaint_file = f"{input_image_file}-inpaint.png"

    inpaint_image_file (input_image_file, black_ink_remove_file, black_ink_add_file, output_inpaint_file)
