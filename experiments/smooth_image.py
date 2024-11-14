import gmic


def smooth_image_file(in_file: str, out_file: str):
    amplitude = 420
    sharpness = 0.5
    anisotropy = 0.6
    alpha = 2.5
    sigma = 5.0
    dl = 0.8
    da = 30
    precision = 2
    interpolation = 0 # nearest
    fast_approx = 1
    repeat = 2
    channels = 0
    smooth_params = (f'{amplitude},'
                     f'{sharpness},'
                     f'{anisotropy},'
                     f'{alpha},'
                     f'{sigma},'
                     f'{dl},'
                     f'{da},'
                     f'{precision},'
                     f'{interpolation},'
                     f'{fast_approx},'
                     f'{repeat},'
                     f'{channels}')

    # print(smooth_params)
    gmic.run(
        f'"{in_file}"'
        f" fx_smooth_anisotropic {smooth_params}"
        f" -threshold[-1] 100,1 normalize[-1] 0,255"
        f' -output[-1] "{out_file}"'
    )
