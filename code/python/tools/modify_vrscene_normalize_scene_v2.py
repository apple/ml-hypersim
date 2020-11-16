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



print("[HYPERSIM: MODIFY_VRSCENE_NORMALIZE_SCENE_V2] Begin...")



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



#
# Exporting programmatically in silent mode is equivalent to the following responses when opening a
# legacy V-Ray scene:
#
# "Do you want gamma/LUT correction to be DISABLED to correspond with the setting in this file?"
#
# YES
#
# "This file was created with an older version of the V-Ray renderer. The DMC sampler Noise threshold
# parameter may need to be increased in order to get similar results and render times.
#
# For more information about other changes in this build of V-Ray please consult the documentation or
# write to support@chaosgroup.com"
#
# OK
#
# "This version of V-Ray includes updated models for VRaySun, VRaySky, VRayPhysicalCamera, and
# VRayLight. Would you like to use the updated models?
# 
# If you choose No, these plugins will render in the same way as with previous versions.
#
# (You can also change this later from the 'Global switches' rollout.)"
#
# NO
#
# "This version of V-Ray includes automatic subdivs calculations, updated internal spectral RGB color
# space and other improvements.
#
# (Note: for best results, reset all render settings to their defaults.)
#
# If you choose Yes, your scene may render slightly differently and may need additional adjustments. 
# If you choose No, your scene will render the same way as with previous versions.
#
# For more information about other changes in this build of V-Ray please consult the documentation or
# write to support@chaosgroup.com"
#
# NO
#
# "The Unit Scale of the file does not match the System Unit Scale.
#
# Do you want to:
#   Rescale the File Objects to the System Unit Scale?
#   Adopt the File's Unit Scale"
#
# ADOPT THE FILE'S UNIT SCALE
#



#
# This modification is equivalent to responding "NO" to the following question:
#
# "Do you want gamma/LUT correction to be DISABLED to correspond with the setting in this file?"
#

bitmap_buffers = renderer.classes.BitmapBuffer.getInstances()
for bitmap_buffer in bitmap_buffers:
    bitmap_buffer.gamma = 0.4545454




#
# This modification is equivalent to responding "YES" to the following question:
#
# "This version of V-Ray includes updated models for VRaySun, VRaySky, VRayPhysicalCamera, and
# VRayLight. Would you like to use the updated models?
# 
# If you choose No, these plugins will render in the same way as with previous versions.
#
# (You can also change this later from the 'Global switches' rollout.)"
#

settings_units_info = renderer.classes.SettingsUnitsInfo.getInstanceOrCreate()
settings_units_info.photometric_scale = 0.002094395




#
# This modification is equivalent to responding "YES" to the following question:
#
# "This version of V-Ray includes automatic subdivs calculations, updated internal spectral RGB color
# space and other improvements.
#
# (Note: for best results, reset all render settings to their defaults.)
#
# If you choose Yes, your scene may render slightly differently and may need additional adjustments. 
# If you choose No, your scene will render the same way as with previous versions.
#
# For more information about other changes in this build of V-Ray please consult the documentation or
# write to support@chaosgroup.com"
#
#
# settings_units_info = renderer.classes.SettingsUnitsInfo.getInstanceOrCreate()
# settings_units_info.rgb_color_space = 1
#
# settings_gi = renderer.classes.SettingsGI.getInstanceOrCreate()
# settings_gi.reflect_caustics = 1
#
# settings_image_sampler = renderer.classes.SettingsImageSampler.getInstanceOrCreate()
# settings_image_sampler.min_shade_rate = 6
#
# settings_dmc_sampler = renderer.classes.SettingsDMCSampler.getInstanceOrCreate()
# settings_dmc_sampler.use_local_subdivs = 0
#



#
# This modification fixes an issue where a rendered image will only match a reference render if the sRGB
# button in the V-Ray GUI is switched off. But it may be switched on by default, so we switch it off here.
#

settings_vfb = renderer.classes.SettingsVFB.getInstanceOrCreate()
settings_vfb.cc_settings  = -1 # overwrite cached VFB settings
settings_vfb.display_srgb = 0  # don't apply gamma correction when saving 8-bits-per-channel images



renderer.export(args.out_file)
print("[HYPERSIM: MODIFY_VRSCENE_NORMALIZE_SCENE_V2] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_NORMALIZE_SCENE_V2] Finished.")
