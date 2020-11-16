#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import glob
import os

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
parser.add_argument("--camera_name", required=True)
args = parser.parse_args()



print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] Begin...")



images_dir = os.path.join(args.scene_dir, "images")

in_scene_fileroot            = "scene"
in_rgb_hdf5_dir              = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_hdf5")
in_rgb_hdf5_files            = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_hdf5", "frame.*.color.hdf5")
in_render_entity_id_hdf5_dir = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_geometry_hdf5")
out_preview_dir              = os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_final_preview")

if not os.path.exists(out_preview_dir): os.makedirs(out_preview_dir)



in_filenames = [ os.path.basename(f) for f in sort(glob.glob(in_rgb_hdf5_files)) ]

for in_filename in in_filenames:

    in_file_root = in_filename.replace(".color.hdf5", "")

    in_rgb_hdf5_file              = os.path.join(in_rgb_hdf5_dir, in_filename)
    in_render_entity_id_hdf5_file = os.path.join(in_render_entity_id_hdf5_dir, in_file_root + ".render_entity_id.hdf5")
    out_rgb_tm_jpg_file           = os.path.join(out_preview_dir, in_file_root + ".tonemap.jpg")

    try:
        with h5py.File(in_rgb_hdf5_file, "r") as f: rgb_color = f["dataset"][:].astype(float32)
    except:
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]") 
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] WARNING: COULD NOT LOAD COLOR IMAGE: " + in_rgb_hdf5_file + "...")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        continue

    try:
        with h5py.File(in_render_entity_id_hdf5_file, "r") as f: render_entity_id = f["dataset"][:].astype(int32)
    except:
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]") 
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] WARNING: COULD NOT LOAD RENDER ENTITY ID IMAGE: " + in_render_entity_id_hdf5_file + "...")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP]")
        continue

    #
    # compute brightness according to "CCIR601 YIQ" method, use CGIntrinsics strategy for tonemapping, see [1,2]
    # [1] https://github.com/snavely/pbrs_tonemapper/blob/master/tonemap_rgbe.py
    # [2] https://landofinterruptions.co.uk/manyshades
    #

    assert all(render_entity_id != 0)

    gamma                             = 1.0/2.2   # standard gamma correction exponent
    inv_gamma                         = 1.0/gamma
    percentile                        = 90        # we want this percentile brightness value in the unmodified image...
    brightness_nth_percentile_desired = 0.8       # ...to be this bright after scaling

    valid_mask = render_entity_id != -1

    if count_nonzero(valid_mask) == 0:
        scale = 1.0 # if there are no valid pixels, then set scale to 1.0
    else:
        brightness       = 0.3*rgb_color[:,:,0] + 0.59*rgb_color[:,:,1] + 0.11*rgb_color[:,:,2] # "CCIR601 YIQ" method for computing brightness
        brightness_valid = brightness[valid_mask]

        eps                               = 0.0001 # if the kth percentile brightness value in the unmodified image is less than this, set the scale to 0.0 to avoid divide-by-zero
        brightness_nth_percentile_current = np.percentile(brightness_valid, percentile)

        if brightness_nth_percentile_current < eps:
            scale = 0.0
        else:

            # Snavely uses the following expression in the code at https://github.com/snavely/pbrs_tonemapper/blob/master/tonemap_rgbe.py:
            # scale = np.exp(np.log(brightness_nth_percentile_desired)*inv_gamma - np.log(brightness_nth_percentile_current))
            #
            # Our expression below is equivalent, but is more intuitive, because it follows more directly from the expression:
            # (scale*brightness_nth_percentile_current)^gamma = brightness_nth_percentile_desired

            scale = np.power(brightness_nth_percentile_desired, inv_gamma) / brightness_nth_percentile_current

    rgb_color_tm = np.power(np.maximum(scale*rgb_color,0), gamma)

    print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] Saving output file: " + out_rgb_tm_jpg_file + " (scale=" + str(scale) + ")")

    imsave(out_rgb_tm_jpg_file, clip(rgb_color_tm,0,1))



print("[HYPERSIM: SCENE_GENERATE_IMAGES_TONEMAP] Finished.")
