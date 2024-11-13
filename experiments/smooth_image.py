import gmic


def smooth_image_file(in_file: str, out_file: str):
    # TODO: Explain or constify these params.
    smooth_params = '427,0.496,0.581,2.48,5.3,0.328,59.17,0.9379,0,1,2,0,"0",nan,nan'
    gmic.run(
        f'"{in_file}"'
        f" -repeat 5 fx_smooth_anisotropic {smooth_params} -done"
        f" -threshold[-1] 100,1 normalize[-1] 0,255"
        f' -output[-1] "{out_file}"'
    )  # smooth latest - very good

    # gmic.run(
    #     f'"{in_file}" -repeat 5 -smooth 10,0,1,1,2 -done -output[-1] "{out_file}"'
    # )  # smooth0
    # gmic.run(f'"{in_file}" smooth 10,0,1,1,2 output "{out_file}"') # smooth0
    # gmic.run(f'"{in_file}" smooth 50,0,1,1,2 output "{out_file}"') # smooth1
    # gmic.run(f'"{in_file}" fx_smooth_median 8,255,0,"0",nan,nan output "{out_file}"')
    # gmic.run(f'"{in_file}" -fx_smooth_anisotropic "80","0.5","0.3","2","5.1","0.8","70.81","2","2","1","1","0","0","50","50" output "{out_file}"')
