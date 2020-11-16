#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import inspect
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--camera_names")
parser.add_argument("--img_name", required=True)
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert \
    args.img_name == "depth_meters" or \
    args.img_name == "normal_cam" or \
    args.img_name == "normal_world" or \
    args.img_name == "render_entity_id" or \
    args.img_name == "semantic" or \
    args.img_name == "semantic_instance" or \
    args.img_name == "color" or \
    args.img_name == "diff" or \
    args.img_name == "diffuse_illumination" or \
    args.img_name == "diffuse_reflectance" or \
    args.img_name == "gamma" or \
    args.img_name == "lambertian" or \
    args.img_name == "non_lambertian" or \
    args.img_name == "residual" or \
    args.img_name == "tonemap"

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_ANIMATIONS] Begin...")



in_scene_fileroot  = "scene"
dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")
animations_dir     = os.path.join(args.dataset_dir, "animations")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



if not os.path.exists(animations_dir): os.makedirs(animations_dir)



# geometry pass
if args.img_name == "depth_meters":
    render_pass = "geometry"
    img_ext     = "png"
if args.img_name == "normal_cam":
    render_pass = "geometry"
    img_ext     = "png"
if args.img_name == "normal_world":
    render_pass = "geometry"
    img_ext     = "png"
if args.img_name == "render_entity_id":
    render_pass = "geometry"
    img_ext     = "png"
if args.img_name == "semantic":
    render_pass = "geometry"
    img_ext     = "png"
if args.img_name == "semantic_instance":
    render_pass = "geometry"
    img_ext     = "png"

# final pass
if args.img_name == "color":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "diff":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "diffuse_illumination":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "diffuse_reflectance":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "lambertian":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "non_lambertian":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "residual":
    render_pass = "final"
    img_ext     = "jpg"
if args.img_name == "tonemap":
    render_pass = "final"
    img_ext     = "jpg"

for s in scenes:

    scene_name    = s["name"]
    detail_dir    = os.path.join(dataset_scenes_dir, scene_name, "_detail")
    images_dir    = os.path.join(dataset_scenes_dir, scene_name, "images")

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df = pd.read_csv(metadata_cameras_csv_file)

    if args.camera_names is not None:
        cameras = [ c for c in df.to_records() if fnmatch.fnmatch(c["camera_name"], args.camera_names) ]
    else:
        cameras = df.to_records()

    for c in cameras:

        camera_name = c["camera_name"]

        print("[HYPERSIM: DATASET_GENERATE_ANIMATIONS] For scene " + scene_name + ", generating animation for camera " + camera_name + "...")

        in_img_file        = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_" + render_pass + "_preview", "frame.%04d." + args.img_name + "." + img_ext))
        out_animation_file = os.path.abspath(os.path.join(animations_dir, scene_name + "_" + camera_name + "_" + args.img_name + ".mp4"))

        cmd = \
            _system_config.animation_bin   + \
            " -y -r 5 "                    + \
            "-i "                          + in_img_file + \
            " -c:v "                       + \
            _system_config.animation_codec + \
            " "                            + out_animation_file
        print("")
        print(cmd)
        print("")
        retval = os.system(cmd)
        assert retval == 0



print("[HYPERSIM: DATASET_GENERATE_ANIMATIONS] Finished.")
