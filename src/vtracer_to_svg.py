from vtracer import convert_image_to_svg_py

DECIMALS = 3


def image_file_to_svg(in_file: str, out_file: str):
    convert_image_to_svg_py(
        in_file,
        out_file,
        colormode="binary",
        path_precision=DECIMALS,
        mode="spline",
        filter_speckle=2,
        layer_difference=16,
        max_iterations=10,
        splice_threshold=45,
    )
