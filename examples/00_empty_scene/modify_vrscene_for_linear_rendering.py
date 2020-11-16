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



print("Begin...")



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

# SettingsEXR
settings_exr = renderer.classes.SettingsEXR.getInstanceOrCreate()
settings_exr.bits_per_channel = 32 # set 32-bits-per-channel for EXR images

# SettingsColorMapping
settings_color_mapping = renderer.classes.SettingsColorMapping.getInstanceOrCreate()
settings_color_mapping.type              = 0 # set color mapping type to "linear multiply"
settings_color_mapping.affect_background = 1
settings_color_mapping.dark_mult         = 1.0 # recommended by Vlado @ Chaos Group
settings_color_mapping.bright_mult       = 1.0 # recommended by Vlado @ Chaos Group
# settings_color_mapping.gamma             = 2.2 # not used
settings_color_mapping.subpixel_mapping  = 0
settings_color_mapping.clamp_output      = 0 # don't clamp the rendering output (recommended by Vlado @ Chaos Group)
# settings_color_mapping.clamp_level       = 1 # not used
settings_color_mapping.adaptation_only   = 2 # only color mapping is applied (recommended by Vlado @ Chaos Group)
settings_color_mapping.linearWorkflow    = 0 # configures a setting for legacy scenes that we don't need, so turn off

# SettingsVFB
settings_vfb = renderer.classes.SettingsVFB.getInstanceOrCreate()
settings_vfb.cc_settings  = -1 # overwrite cached VFB settings
settings_vfb.display_srgb = 0  # don't apply gamma correction when saving 8-bits-per-channel images

renderer.export(args.out_file)
print("Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("Finished.")
