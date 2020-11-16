#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import ntpath
import os
import posixpath
import time
import vray

parser = argparse.ArgumentParser()
parser.add_argument("--in_file", required=True)
parser.add_argument("--out_file", required=True)
parser.add_argument("--light_cache_name", required=True)
parser.add_argument("--irradiance_map_name", required=True)
parser.add_argument("--shared_asset_dir", required=True)
parser.add_argument("--platform_when_rendering", required=True)
parser.add_argument("--shared_asset_dir_when_rendering", required=True)
args = parser.parse_args()

assert os.path.exists(args.in_file)
assert args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix" or args.platform_when_rendering == "windows"

if args.platform_when_rendering == "mac" or args.platform_when_rendering == "unix":
    os_path_module_when_rendering = posixpath
else:
    os_path_module_when_rendering = ntpath



print("[HYPERSIM: MODIFY_VRSCENE_LOAD_GI_CACHE_FILES] Begin...")



irradiance_map_file_when_rendering = os_path_module_when_rendering.join(args.shared_asset_dir_when_rendering, args.irradiance_map_name + ".vrmap")
light_cache_file_when_rendering    = os_path_module_when_rendering.join(args.shared_asset_dir_when_rendering, args.light_cache_name    + ".vrlmap")

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

# SettingsLightCache
settings_light_cache = renderer.classes.SettingsLightCache.getInstanceOrCreate()
settings_light_cache.mode           = 2 # from file
settings_light_cache.file           = light_cache_file_when_rendering
settings_light_cache.auto_save      = 0 # don't auto-save the result
settings_light_cache.auto_save_file = ""

# SettingsIrradianceMap
settings_irradiance_map = renderer.classes.SettingsIrradianceMap.getInstanceOrCreate()
settings_irradiance_map.mode           = 2 # from file
settings_irradiance_map.file           = irradiance_map_file_when_rendering
settings_irradiance_map.auto_save      = 0 # don't auto-save the result
settings_irradiance_map.auto_save_file = ""
        
renderer.export(args.out_file)
print("[HYPERSIM: MODIFY_VRSCENE_LOAD_GI_CACHE_FILES] Exported vrscene successfully.")

renderer.close()
time.sleep(0.5)



print("[HYPERSIM: MODIFY_VRSCENE_LOAD_GI_CACHE_FILES] Finished.")
