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
parser.add_argument("--frames")
parser.add_argument("--render_pass")
parser.add_argument("--n_jobs", type=int)
parser.add_argument("--denoise", action="store_true")
parser.add_argument("--use_single_threaded_reference_implementation", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)

if args.render_pass is not None:
    assert args.render_pass == "geometry" or args.render_pass == "final"

if args.render_pass == "geometry":
    assert not args.denoise

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_HDF5_FROM_VRIMG] Begin...")



if not args.use_single_threaded_reference_implementation:
    if args.n_jobs is not None:
        n_jobs = args.n_jobs
    else:
        n_jobs = 4 # 4 parallel jobs by default; more processes don't seem to offer much speed-up
        
in_scene_fileroot  = "scene"
dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



def process_scene(s, args):

    scene_name = s["name"]
    tmp_dir    = os.path.join(dataset_scenes_dir, scene_name, "_tmp")
    detail_dir = os.path.join(dataset_scenes_dir, scene_name, "_detail")
    images_dir = os.path.join(dataset_scenes_dir, scene_name, "images")

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df = pd.read_csv(metadata_cameras_csv_file)

    if args.camera_names is not None:
        cameras = [ c for c in df.to_records() if fnmatch.fnmatch(c["camera_name"], args.camera_names) ]
    else:
        cameras = df.to_records()

    for c in cameras:

        camera_name = c["camera_name"]

        print("[HYPERSIM: DATASET_GENERATE_HDF5_FROM_VRIMG] For scene " + scene_name + ", generating HDF5 files for camera " + camera_name + "...")

        #
        # generate HDF5 files for geometry render
        #

        if args.render_pass is None or args.render_pass == "geometry":

            if args.frames is not None:
                in_vrimg_files = '"' + os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry", "frame." + args.frames + ".vrimg")) + '"'
            else:
                in_vrimg_files = '"' + os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry", "frame.*.vrimg")) + '"'

            in_camera_trajectory_dir = os.path.abspath(os.path.join(detail_dir, camera_name))
            in_metadata_nodes_file   = os.path.abspath(os.path.join(detail_dir, "metadata_nodes.csv"))
            in_metadata_scene_file   = os.path.abspath(os.path.join(detail_dir, "metadata_scene.csv"))
            out_hdf5_dir             = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry_hdf5"))
            out_preview_dir          = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry_preview"))
            tmp_dir_                 = os.path.abspath(tmp_dir)

            current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
            cwd = os.getcwd()
            os.chdir(current_source_file_path)

            cmd = \
                _system_config.python_bin + " generate_hdf5_from_vrimg.py" + \
                " --in_vrimg_files "           + in_vrimg_files           + \
                " --in_camera_trajectory_dir " + in_camera_trajectory_dir + \
                " --in_metadata_nodes_file "   + in_metadata_nodes_file   + \
                " --in_metadata_scene_file "   + in_metadata_scene_file   + \
                " --out_hdf5_dir "             + out_hdf5_dir             + \
                " --out_preview_dir "          + out_preview_dir          + \
                " --tmp_dir "                  + tmp_dir_                 + \
                " --render_pass geometry"
            print("")
            print(cmd)
            print("")
            retval = os.system(cmd)
            assert retval == 0

            os.chdir(cwd)

        #
        # generate HDF5 files for final render
        #

        if args.render_pass is None or args.render_pass == "final":
            
            if args.frames is not None:
                in_vrimg_files = '"' + os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_final", "frame." + args.frames + ".vrimg")) + '"'
            else:
                in_vrimg_files = '"' + os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_final", "frame.*.vrimg")) + '"'

            out_hdf5_dir    = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_final_hdf5"))
            out_preview_dir = os.path.abspath(os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_final_preview"))
            tmp_dir_        = os.path.abspath(tmp_dir)

            if args.denoise:
                denoise_arg = " --denoise"
            else:
                denoise_arg = ""

            current_source_file_path = path_utils.get_current_source_file_path(frame=inspect.currentframe())
            cwd = os.getcwd()
            os.chdir(current_source_file_path)

            cmd = \
                _system_config.python_bin + " generate_hdf5_from_vrimg.py" + \
                " --in_vrimg_files "   + in_vrimg_files  + \
                " --out_hdf5_dir "     + out_hdf5_dir    + \
                " --out_preview_dir "  + out_preview_dir + \
                " --tmp_dir "          + tmp_dir_        + \
                " --render_pass final" + \
                denoise_arg
            print("")
            print(cmd)
            print("")
            retval = os.system(cmd)
            assert retval == 0

            os.chdir(cwd)



if args.use_single_threaded_reference_implementation:
    for s in scenes:
        process_scene(s, args)

if not args.use_single_threaded_reference_implementation:
    from joblib import Parallel, delayed
    Parallel(n_jobs=n_jobs, verbose=10)(delayed(process_scene)(s, args) for s in scenes)



print("[HYPERSIM: DATASET_GENERATE_HDF5_FROM_VRIMG] Finished.")
