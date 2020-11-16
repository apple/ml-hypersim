#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import cv2
import glob
import os

parser = argparse.ArgumentParser()
parser.add_argument("--in_files", required=True)
parser.add_argument("--out_dir", required=True)
parser.add_argument("--tone_mapping_mode", required=True)
parser.add_argument("--gamma_correction", action="store_true")
args = parser.parse_args()

assert args.tone_mapping_mode == "linear" or args.tone_mapping_mode == "exponential"



print("Begin...")



input_dir = os.path.dirname(args.in_files)
if input_dir == "":
    input_dir = "."

assert os.path.exists(input_dir)

if not os.path.exists(args.out_dir): os.makedirs(args.out_dir)



in_filenames = [ os.path.basename(f) for f in sort(glob.glob(args.in_files)) ]

for in_filename in in_filenames:

    in_file          = os.path.join(input_dir, in_filename)
    in_filename_root = os.path.splitext(in_filename)[0]
    in_filename_ext  = os.path.splitext(in_filename)[1]
    out_file         = os.path.join(args.out_dir, in_filename_root + ".jpg")

    print("Saving " + out_file + "...")

    # load file
    in_rgb_color = cv2.imread(in_file, cv2.IMREAD_UNCHANGED)[:,:,[2,1,0]]

    # apply color mapping with sensible default parameters that are equivalent to V-Ray's "exponential mode"
    if args.tone_mapping_mode == "exponential":

        rgb_color          = in_rgb_color.copy()
        dark_mult          = 2.3
        bright_mult        = 2.3
        k                  = clip(rgb_color,0,1)
        k                  = dark_mult*(1.0-k) + bright_mult*k
        rgb_color_exp      = 1.0 - exp(-rgb_color*k)

        out_rgb_color = rgb_color_exp

    if args.tone_mapping_mode == "linear":

        out_rgb_color = in_rgb_color.copy()

    in_rgb_color = out_rgb_color

    # apply gamma correction with sensible default parameters
    if args.gamma_correction:

        rgb_color       = in_rgb_color.copy()
        gamma           = 1.0/2.2
        rgb_color_gamma = np.power(np.maximum(rgb_color,0), gamma)

        out_rgb_color = rgb_color_gamma

    in_rgb_color = out_rgb_color

    # clip
    rgb_color      = in_rgb_color.copy()
    rgb_color_clip = clip(rgb_color,0,1)

    out_rgb_color = rgb_color_clip

    imsave(out_file, out_rgb_color)



print("Finished.")
