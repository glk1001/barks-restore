import gmic

def smooth_image_file(in_file: str, out_file: str):
    # TODO: Get the right smoothing params here
    gmic.run(f'"{in_file}" -repeat 5 -smooth 10,0,1,1,2 -done -output[-1] "{out_file}"') # smooth0
    #gmic.run(f'"{in_file}" smooth 10,0,1,1,2 output "{out_file}"') # smooth0
    #gmic.run(f'"{in_file}" smooth 50,0,1,1,2 output "{out_file}"') # smooth1
    # gmic.run(f'"{in_file}" fx_smooth_median 8,255,0,"0",nan,nan output "{out_file}"')
    #gmic.run(f'"{in_file}" -fx_smooth_anisotropic "80","0.5","0.3","2","5.1","0.8","70.81","2","2","1","1","0","0","50","50" output "{out_file}"')
