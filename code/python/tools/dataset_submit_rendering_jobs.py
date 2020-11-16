#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import fnmatch
import inspect
import os
import pandas as pd
import re

import path_utils

path_utils.add_path_to_sys_path("..", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import _system_config

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--camera_names")
parser.add_argument("--render_pass", required=True)
parser.add_argument("--frames", help="e.g., 0 or 0:100 or 0:100:10")
parser.add_argument("--skip_post_task_script", action="store_true")
parser.add_argument("--start_render_jobs_immediately", action="store_true")
args = parser.parse_args()

dataset_dir = os.path.abspath(args.dataset_dir)

assert os.path.exists(dataset_dir)
assert args.render_pass == "pre" or args.render_pass == "geometry" or args.render_pass == "final"

path_utils.add_path_to_sys_path(dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_SUBMIT_RENDERING_JOBS] Begin...")



if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



hypersim_platform_when_submitting_key    = "ExtraInfo0"
hypersim_dataset_dir_when_submitting_key = "ExtraInfo1"
hypersim_scene_name_key                  = "ExtraInfo2"
hypersim_camera_name_key                 = "ExtraInfo3"
hypersim_render_pass_key                 = "ExtraInfo4"
hypersim_output_file_root_key            = "ExtraInfo5"
hypersim_output_file_ext_key             = "ExtraInfo6"
hypersim_post_task_script                = os.path.join(path_utils.get_current_source_file_path(frame=inspect.currentframe()), _system_config.cloud_post_task_script)

if args.render_pass == "geometry": output_file_ext = "vrimg" 
if args.render_pass == "pre":      output_file_ext = "jpg"
if args.render_pass == "final":    output_file_ext = "vrimg"

output_file_root = "frame"
output_file      = output_file_root + "." + output_file_ext



for s in scenes:

    scene_name = s["name"]
    detail_dir = os.path.join(dataset_dir, "scenes", scene_name, "_detail")
    jobs_dir   = os.path.join(dataset_dir, "scenes", scene_name, "jobs")

    if not os.path.exists(jobs_dir): os.makedirs(jobs_dir)

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df = pd.read_csv(metadata_cameras_csv_file)

    if args.camera_names is not None:
        cameras = [ c for c in df.to_records() if fnmatch.fnmatch(c["camera_name"], args.camera_names) ]
    else:
        cameras = df.to_records()

    for c in cameras:

        camera_name = c["camera_name"]
        camera_dir  = os.path.join(detail_dir, camera_name)

        camera_keyframe_frame_indices_hdf5_file = os.path.join(camera_dir, "camera_keyframe_frame_indices.hdf5")

        with h5py.File(camera_keyframe_frame_indices_hdf5_file, "r") as f: camera_keyframe_frame_indices = f["dataset"][:]

        if args.frames is not None:
            output_frames = args.frames.split(":")
            assert len(output_frames) == 1 or len(output_frames) == 2 or len(output_frames) == 3
            if len(output_frames) == 1:
                output_frames = output_frames[0]
            elif len(output_frames) == 2:
                output_frames = output_frames[0] + ":" + str(int(output_frames[1]) - 1)
            elif len(output_frames) == 3:
                output_frames = output_frames[0] + ":" + str(int(output_frames[1]) - 1) + ":" + output_frames[2]
        else:
            output_frames = "0:" + str(camera_keyframe_frame_indices[-1])

        if args.render_pass == "geometry":
            job_name           = scene_name + "@" + "scene_" + camera_name + "_geometry"
            vrscene_file       = os.path.join(dataset_dir, "scenes", scene_name, "vrscenes", "scene_" + camera_name + "_geometry.vrscene")
            output_dir         = os.path.join(dataset_dir, "scenes", scene_name, "images",   "scene_" + camera_name + "_geometry")
            job_file           = os.path.join(dataset_dir, "scenes", scene_name, "jobs",     "scene_" + camera_name + "_geometry.txt")

        if args.render_pass == "pre":
            job_name           = scene_name + "@" + "scene_" + camera_name + "_pre"
            vrscene_file       = os.path.join(dataset_dir, "scenes", scene_name, "vrscenes", "scene_" + camera_name + "_pre.vrscene")
            output_dir         = os.path.join(dataset_dir, "scenes", scene_name, "images",   "scene_" + camera_name + "_pre")
            job_file           = os.path.join(dataset_dir, "scenes", scene_name, "jobs",     "scene_" + camera_name + "_pre.txt")

        if args.render_pass == "final":
            job_name           = scene_name + "@" + "scene_" + camera_name + "_final"
            vrscene_file       = os.path.join(dataset_dir, "scenes", scene_name, "vrscenes", "scene_" + camera_name + "_final.vrscene")
            output_dir         = os.path.join(dataset_dir, "scenes", scene_name, "images",   "scene_" + camera_name + "_final")
            job_file           = os.path.join(dataset_dir, "scenes", scene_name, "jobs",     "scene_" + camera_name + "_final.txt")

        output_filepath = os.path.join(output_dir, output_file)

        auxiliary_camera_keyframe_frame_indices_hdf5_file = os.path.join(dataset_dir, "scenes", scene_name, "_detail", camera_name, "camera_keyframe_frame_indices.hdf5")
        auxiliary_camera_keyframe_positions_hdf5_file     = os.path.join(dataset_dir, "scenes", scene_name, "_detail", camera_name, "camera_keyframe_positions.hdf5")
        auxiliary_camera_keyframe_orientations_hdf5_file  = os.path.join(dataset_dir, "scenes", scene_name, "_detail", camera_name, "camera_keyframe_orientations.hdf5")
        auxiliary_metadata_nodes_csv_file                 = os.path.join(dataset_dir, "scenes", scene_name, "_detail", "metadata_nodes.csv")
        auxiliary_metadata_scene_csv_file                 = os.path.join(dataset_dir, "scenes", scene_name, "_detail", "metadata_scene.csv")

        if args.start_render_jobs_immediately:
            initial_status = "Active"
        else:
            initial_status = "Suspended"

        if not args.skip_post_task_script:
            job_info = {
                "Name"                                   : job_name,
                "UserName"                               : _system_config.cloud_server_username,
                "Frames"                                 : output_frames,
                "Plugin"                                 : "Vray",
                "OutputDirectory0"                       : output_dir,
                "OutputFilename0"                        : output_file,
                "InitialStatus"                          : initial_status,
                "PostTaskScript"                         : hypersim_post_task_script,
                hypersim_platform_when_submitting_key    : "windows",
                hypersim_dataset_dir_when_submitting_key : dataset_dir,
                hypersim_scene_name_key                  : scene_name,
                hypersim_camera_name_key                 : camera_name,
                hypersim_render_pass_key                 : args.render_pass,
                hypersim_output_file_root_key            : output_file_root,
                hypersim_output_file_ext_key             : output_file_ext }
        else:
            job_info = {
                "Name"                                   : job_name,
                "UserName"                               : _system_config.cloud_server_username,
                "Frames"                                 : output_frames,
                "Plugin"                                 : "Vray",
                "OutputDirectory0"                       : output_dir,
                "OutputFilename0"                        : output_file,
                "InitialStatus"                          : initial_status }

        plugin_info = {
            "InputFilename"      : vrscene_file,
            "OutputFilename"     : output_filepath,
            "VRayEngine"         : "V-Ray",
            "OverrideResolution" : False }

        auxiliary_files = [
            auxiliary_camera_keyframe_frame_indices_hdf5_file,
            auxiliary_camera_keyframe_positions_hdf5_file,
            auxiliary_camera_keyframe_orientations_hdf5_file,
            auxiliary_metadata_nodes_csv_file,
            auxiliary_metadata_scene_csv_file ]



        # parse the vrscene file, extract all file references, add them to cloud pre-cache list
        print("[HYPERSIM: DATASET_SUBMIT_RENDERING_JOBS] Extracting all file references from " + vrscene_file + "...")

        cloud_pre_cache_files = [ vrscene_file ]
        files_to_visit        = [ vrscene_file ]

        cloud_pre_cache_files_initial_tokens = [ "file", "ies_file", "#include" ]
        files_to_visit_initial_tokens        = [ "#include" ]

        while len(files_to_visit) > 0:
            file_to_visit = files_to_visit.pop(0)
            with open(file_to_visit, "r") as f:
                lines = f.readlines()
            for line_ in lines:
                line = line_.strip()
                for initial_token in cloud_pre_cache_files_initial_tokens:
                    if line.startswith(initial_token):
                        cloud_pre_cache_file_tokens = [ t.strip() for t in re.split('=|;|"', line) if t.strip() != "" ]
                        if len(cloud_pre_cache_file_tokens) == 2:
	                        cloud_pre_cache_file = cloud_pre_cache_file_tokens[1]
	                        cloud_pre_cache_files.append(cloud_pre_cache_file)
                        elif len(cloud_pre_cache_file_tokens) > 2:
                            print("[HYPERSIM: DATASET_SUBMIT_RENDERING_JOBS] WARNING: Couldn't understand filename in text: " + line)
                for initial_token in files_to_visit_initial_tokens:
                    if line.startswith(initial_token):
                        files_to_visit_tokens = [ t.strip() for t in re.split('=|;|"', line) if t.strip() != "" ]
                        assert len(files_to_visit_tokens) == 2
                        file_to_visit = files_to_visit_tokens[1]
                        files_to_visit.append(file_to_visit)

        cloud_pre_cache_files = set(cloud_pre_cache_files)
        i = 0
        for f in cloud_pre_cache_files:

            # # V-Ray can handle mixed slashes in paths, so we don't bother correcting this elsewhere in the pipeline.
            # # But we want to be extra careful when submitting jobs for cloud rendering, so we correct slashes here.
            # f_ = f.replace("/", "\\")
            f_ = f.replace("\\","/")

            job_info[_system_config.cloud_asset_key_prefix_str + str(i)] = f_
            i = i+1

        with open(job_file, "w") as f:
            f.write(str(job_info) + "\n\n")
            f.write(str(plugin_info) + "\n\n")
            f.write(str(auxiliary_files) + "\n")

        print("[HYPERSIM: DATASET_SUBMIT_RENDERING_JOBS] Submitting job " + job_name + "...")



print("[HYPERSIM: DATASET_SUBMIT_RENDERING_JOBS] Finished.")
