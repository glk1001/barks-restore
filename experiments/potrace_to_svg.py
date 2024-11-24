import cairosvg
from PIL import Image
from potrace import Bitmap, POTRACE_TURNPOLICY_MINORITY

Image.MAX_IMAGE_PIXELS = None
DECIMALS = 3


def image_file_to_svg(in_file: str, out_file: str):
    image = Image.open(in_file)
    bitmap = Bitmap(image, blacklevel=0.5)

    plist = bitmap.trace(
        turdsize=2,
        turnpolicy=POTRACE_TURNPOLICY_MINORITY,
        alphamax=1.2,
        opticurve=True,
        opttolerance=1.0,
    )

    parts = []
    for curve in plist:
        fs = curve.start_point
        parts.append(f"M{fs.x:.{DECIMALS}f},{fs.y:.{DECIMALS}f}")

        for segment in curve.segments:
            if segment.is_corner:
                a = segment.c
                b = segment.end_point
                parts.append(
                    f"L{a.x:.{DECIMALS}f},{a.y:.{DECIMALS}f}"
                    f"L{b.x:.{DECIMALS}f},{b.y:.{DECIMALS}f}"
                )
            else:
                a = segment.c1
                b = segment.c2
                c = segment.end_point
                parts.append(
                    f"C{a.x:.{DECIMALS}f},{a.y:.{DECIMALS}f}"
                    f" {b.x:.{DECIMALS}f},{b.y:.{DECIMALS}f}"
                    f" {c.x:.{DECIMALS}f},{c.y:.{DECIMALS}f}"
                )

        parts.append("z")

    with open(out_file, "w") as fp:
        xmlns = "http://www.w3.org/2000/svg"
        xmlns_xlink = "http://www.w3.org/1999/xlink"
        fp.write(
            f'<svg version="1.1"'
            f' xmlns="{xmlns}" xmlns:xlink="{xmlns_xlink}"'
            f' width="{image.width}" height="{image.height}"'
            f' viewBox="0 0 {image.width} {image.height}">'
        )
        fp.write(
            f'<path stroke="none" fill="black" fill-rule="evenodd" d="{"".join(parts)}"/>'
        )
        fp.write("</svg>")


def svg_file_to_png(svg_file: str, png_file: str):
    png_image = cairosvg.svg2png(url=svg_file, scale=1)

    with open(png_file, "wb") as f:
        f.write(png_image)
