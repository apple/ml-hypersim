#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
args = parser.parse_args()

assert os.path.exists(args.scene_dir)



print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_ASSET_EXPORT] Begin...")



# get cameras
metadata_cameras_asset_export_csv_file = os.path.join(args.scene_dir, "_asset_export", "metadata_cameras_asset_export.csv")
df = pd.read_csv(metadata_cameras_asset_export_csv_file)

# for each camera
for c in df.to_records():

    camera_name = c["camera_name"]

    print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_ASSET_EXPORT] Generating trajectory for camera " + camera_name + "...")

    asset_export_dir                        = os.path.join(args.scene_dir, "_asset_export")
    detail_dir                              = os.path.join(args.scene_dir, "_detail")
    camera_csv_file                         = os.path.join(asset_export_dir, camera_name + ".csv")
    camera_dir                              = os.path.join(asset_export_dir, camera_name)
    camera_keyframe_frame_indices_hdf5_file = os.path.join(camera_dir, "camera_keyframe_frame_indices.hdf5")
    camera_keyframe_positions_hdf5_file     = os.path.join(camera_dir, "camera_keyframe_positions.hdf5")
    camera_keyframe_orientations_hdf5_file  = os.path.join(camera_dir, "camera_keyframe_orientations.hdf5")
    metadata_camera_csv_file                = os.path.join(camera_dir, "metadata_camera.csv")

    if not os.path.exists(camera_dir): os.makedirs(camera_dir)

    df_cam        = pd.read_csv(camera_csv_file)
    df_cam_unique = df_cam.drop_duplicates()

    # if camera is static, then compress into a single keyframe
    if df_cam_unique.shape[0] == 1:
        df_cam_ = df_cam_unique
    else:
        df_cam_ = df_cam

    num_keyframes                 = df_cam_.shape[0]
    camera_keyframe_frame_indices = arange(num_keyframes)
    camera_keyframe_positions     = zeros((num_keyframes,3))
    camera_keyframe_orientations  = zeros((num_keyframes,3,3))
    camera_frame_time_seconds     = 1.0

    # for each keyframe
    j = 0
    for params in df_cam_.to_records():
        
        camera_position = array([params["translation_world_from_obj_x"], params["translation_world_from_obj_y"], params["translation_world_from_obj_z"]])
        R_world_from_cam = array([[params["rotation_world_from_obj_00"], params["rotation_world_from_obj_01"], params["rotation_world_from_obj_02"]],
                                  [params["rotation_world_from_obj_10"], params["rotation_world_from_obj_11"], params["rotation_world_from_obj_12"]],
                                  [params["rotation_world_from_obj_20"], params["rotation_world_from_obj_21"], params["rotation_world_from_obj_22"]]])

        camera_keyframe_positions[j]    = camera_position
        camera_keyframe_orientations[j] = R_world_from_cam
        
        j = j+1

    with h5py.File(camera_keyframe_frame_indices_hdf5_file, "w") as f: f.create_dataset("dataset", data=camera_keyframe_frame_indices)
    with h5py.File(camera_keyframe_positions_hdf5_file,     "w") as f: f.create_dataset("dataset", data=camera_keyframe_positions)
    with h5py.File(camera_keyframe_orientations_hdf5_file,  "w") as f: f.create_dataset("dataset", data=camera_keyframe_orientations)

    df_camera = pd.DataFrame(columns=["parameter_name", "parameter_value"], data={"parameter_name": ["frame_time_seconds"], "parameter_value": [camera_frame_time_seconds]})
    df_camera.to_csv(metadata_camera_csv_file, index=False)



print("[HYPERSIM: SCENE_GENERATE_CAMERA_TRAJECTORIES_ASSET_EXPORT] Finished.")
