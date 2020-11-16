#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import os
import inspect
import shlex
import subprocess
import sys

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--dataset_dir_when_rendering")
parser.add_argument("--scene_name")
parser.add_argument("--camera_name")
parser.add_argument("--render_pass", required=True)
parser.add_argument("--frames", help="e.g., 0 or 0:100 or 0:100:10")
parser.add_argument("--normalization_policy")
parser.add_argument("--save_image", action="store_true")
parser.add_argument("--save_gi_cache_files", action="store_true")
parser.add_argument("--reduce_image_quality", action="store_true")
parser.add_argument("--reduce_image_size", action="store_true")
parser.add_argument("--linear_rendering", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert args.render_pass == "geometry" or args.render_pass == "pre" or args.render_pass == "final" or args.render_pass == "none"
if args.normalization_policy is not None:
    assert args.normalization_policy == "v0" or args.normalization_policy == "v1" or args.normalization_policy == "v2"
if args.render_pass == "geometry" or args.render_pass == "pre" or args.render_pass == "final":
    assert args.camera_name is not None



print("[HYPERSIM: SCENE_RENDER] Begin...")



in_scene_fileroot = "scene"
vrscenes_dir      = os.path.join(args.dataset_dir, "scenes", args.scene_name, "vrscenes")
images_dir        = os.path.join(args.dataset_dir, "scenes", args.scene_name, "images")



if args.render_pass == "none":
    scene_file = os.path.abspath(os.path.join(vrscenes_dir, in_scene_fileroot + ".vrscene"))
else:
    assert args.camera_name is not None
    assert args.render_pass is not None
    scene_file = os.path.abspath(os.path.join(vrscenes_dir, in_scene_fileroot + "_" + args.camera_name + "_" + args.render_pass + ".vrscene"))

if args.save_image:
    if args.render_pass == "pre" or args.render_pass == "none":
        img_filename = "frame.jpg"
    else:
        img_filename = "frame.vrimg"

    if args.render_pass == "geometry" or args.render_pass == "pre" or args.render_pass == "final":
        img_file = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + args.camera_name + "_" + args.render_pass, img_filename))
    else:
        img_file = os.path.abspath(os.path.join(images_dir, in_scene_fileroot, img_filename))

    img_file_str = '-imgFile="' + img_file + '"'
else:
    img_file_str = ""

if args.frames is not None:
    frames = args.frames.split(":")
    assert len(frames) == 1 or len(frames) == 2 or len(frames) == 3
    if len(frames) == 1:
        frames = frames[0]
    elif len(frames) == 2:
        frames = frames[0] + "-" + str(int(frames[1]) - 1)
    elif len(frames) == 3:
        frames = frames[0] + "-" + str(int(frames[1]) - 1) + "," + frames[2]
else:
    frames = "0"



parameter_override_str = ""

if args.dataset_dir_when_rendering is not None:
    parameter_override_str = parameter_override_str + ' -remapPath="' + args.dataset_dir_when_rendering + '=' + args.dataset_dir + '"'

    if args.render_pass == "pre":
        parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsLightCache::auto_save_file='    + os.path.join(args.dataset_dir, "scenes", args.scene_name, "_detail", in_scene_fileroot + "_" + args.camera_name + "_shared", "_hypersim_light_cache.%04d.vrlmap") + '"'
        parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsIrradianceMap::auto_save_file=' + os.path.join(args.dataset_dir, "scenes", args.scene_name, "_detail", in_scene_fileroot + "_" + args.camera_name + "_shared", "_hypersim_irradiance_map.%04d.vrmap") + '"'

if args.normalization_policy is not None:
    if args.normalization_policy == "v1": parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsUnitsInfo::photometric_scale=0.002094395"'
    if args.normalization_policy == "v2": parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsUnitsInfo::photometric_scale=0.002094395" -parameterOverride="BitmapBuffer::gamma=0.4545454"'

if not args.save_image:
    parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsOutput::img_file="'

if not args.save_gi_cache_files:
    parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsLightCache::auto_save=0" -parameterOverride="SettingsIrradianceMap::auto_save=0"'

if args.reduce_image_quality:
    parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsImageSampler::type=0" -parameterOverride="SettingsImageSampler::fixed_subdivs=1" -parameterOverride="SettingsImageSampler::fixed_per_pixel_filtering=0" -parameterOverride="SettingsImageSampler::min_shade_rate=1"'

if args.reduce_image_size:
    parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsOutput::img_width=256" -parameterOverride="SettingsOutput::img_height=256"'

if args.linear_rendering:
    parameter_override_str = parameter_override_str + ' -parameterOverride="SettingsColorMapping::type=0" -parameterOverride="SettingsColorMapping::affect_background=1" -parameterOverride="SettingsColorMapping::dark_mult=1.0" -parameterOverride="SettingsColorMapping::bright_mult=1.0" -parameterOverride="SettingsColorMapping::subpixel_mapping=0" -parameterOverride="SettingsColorMapping::clamp_output=0" -parameterOverride="SettingsColorMapping::adaptation_only=2" -parameterOverride="SettingsColorMapping::linearWorkflow=0"'



cmd = _system_config.vray_bin + \
    ' -sceneFile="' + scene_file   + '"' + \
    ' '             + img_file_str + \
    ' -frames='     + frames       + \
    ' '             + parameter_override_str

print("")
print(cmd)
print("")
if sys.platform == "win32":
    retval = subprocess.run(shlex.split(cmd)) # do not use os.system because it doesn't parse command-line arguments cleanly
    retval.check_returncode()
else:
    retval = os.system(cmd)
    assert retval == 0



print("[HYPERSIM: SCENE_RENDER] Finished.")
