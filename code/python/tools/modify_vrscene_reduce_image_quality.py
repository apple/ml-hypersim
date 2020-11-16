#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import time
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)



print("[HYPERSIM: MODIFY_VRSCENE_REDUCE_IMAGE_QUALITY] Begin...")



output_dir = os.path.dirname(args.out_file)
if output_dir == "":
    output_dir = "."

if not os.path.exists(output_dir): os.makedirs(output_dir)



renderer = vray.VRayRenderer()
def log_msg(renderer, message, level, instant):
    print(str(instant) + " " + str(level) + " " + message)
renderer.setOnLogMessage(log_msg)
renderer.load(args.in_file)
time.sleep(0.5)

# SettingsImageSampler
settings_image_sampler = renderer.classes.SettingsImageSampler.getInstanceOrCreate()
settings_image_sampler.type                      = 0
settings_image_sampler.fixed_subdivs             = 1
settings_image_sampler.fixed_per_pixel_filtering = 0
settings_image_sampler.min_shade_rate            = 1
    
# RenderChannelDenoiser
render_channel_denoisers = renderer.classes.RenderChannelDenoiser.getInstances()
for r in render_channel_denoisers:
    r.enabled = 0
        
renderer.export(args.out_file)
print("[HYPERSIM: MODIFY_VRSCENE_REDUCE_IMAGE_QUALITY] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_REDUCE_IMAGE_QUALITY] Finished.")
