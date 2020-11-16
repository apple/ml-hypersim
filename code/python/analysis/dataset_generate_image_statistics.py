#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import fnmatch
import glob
import h5py
import inspect
import os
import pandas as pd
import sklearn.preprocessing

import path_utils

parser = argparse.ArgumentParser()
parser.add_argument("--dataset_dir", required=True)
parser.add_argument("--analysis_dir", required=True)
parser.add_argument("--batch_name", required=True)
parser.add_argument("--bounding_box_type", required=True)
parser.add_argument("--scene_names")
parser.add_argument("--camera_names")
parser.add_argument("--load_snapshot", action="store_true")
args = parser.parse_args()

assert os.path.exists(args.dataset_dir)
assert args.bounding_box_type == "axis_aligned" or args.bounding_box_type == "object_aligned_2d" or args.bounding_box_type == "object_aligned_3d"

path_utils.add_path_to_sys_path(args.dataset_dir, mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Begin...")



dataset_scenes_dir = os.path.join(args.dataset_dir, "scenes")

if args.scene_names is not None:
    scenes = [ s for s in _dataset_config.scenes if fnmatch.fnmatch(s["name"], args.scene_names) ]
else:
    scenes = _dataset_config.scenes



# UNIQUE OBJECTS PER CLASS
# PIXELS PER CLASS
semantic_id_to_name_map = {
    1  : "wall",
    2  : "floor",
    3  : "cabinet",
    4  : "bed",
    5  : "chair",
    6  : "sofa",
    7  : "table",
    8  : "door",
    9  : "window",
    10 : "bookshelf",
    11 : "picture",
    12 : "counter",
    13 : "blinds",
    14 : "desk",
    15 : "shelves",
    16 : "curtain",
    17 : "dresser",
    18 : "pillow",
    19 : "mirror",
    20 : "floormat",
    21 : "clothes",
    22 : "ceiling",
    23 : "books",
    24 : "refrigerator",
    25 : "television",
    26 : "paper",
    27 : "towel",
    28 : "showercurtain",
    29 : "box",
    30 : "whiteboard",
    31 : "person",
    32 : "nightstand",
    33 : "toilet",
    34 : "sink",
    35 : "lamp",
    36 : "bathtub",
    37 : "bag",
    38 : "otherstructure",
    39 : "otherfurniture",
    40 : "otherprop" }

# UNIQUE OBJECTS PER IMAGE
unique_objects_per_image_hist_n_bins    = 10000
unique_objects_per_image_hist_bin_edges = arange(unique_objects_per_image_hist_n_bins+1)

# UNIQUE CLASSES PER IMAGE
unique_classes_per_image_hist_n_bins    = len(semantic_id_to_name_map)+1 # +1 because we want to make room for the value 0
unique_classes_per_image_hist_bin_edges = arange(unique_classes_per_image_hist_n_bins+1)

# UNIQUE OBJECTS PER CLASS
# PIXELS PER CLASS
per_class_hist_n_bins         = len(semantic_id_to_name_map) + 2 # +2 because we want to make room for the values 0 and -1
per_class_hist_min_bin_center = -1
per_class_hist_max_bin_center = len(semantic_id_to_name_map)

# DEPTH (LINEAR)
depth_hist_linear_n_bins    = 1000
depth_hist_linear_min       = 0.0
depth_hist_linear_max       = 20.0
depth_hist_linear_bin_edges = linspace(depth_hist_linear_min, depth_hist_linear_max, depth_hist_linear_n_bins+1)

# DEPTH (LOG)
depth_hist_log_n_bins    = 1000
depth_hist_log_base      = 10.0
depth_hist_log_min       = -2.0 # 0.01
depth_hist_log_max       = 3.0  # 1000.0
depth_hist_log_bin_edges = logspace(depth_hist_log_min, depth_hist_log_max, depth_hist_log_n_bins+1, base=depth_hist_log_base)

# NORMAL
normal_hist_n_bins    = 100
normal_hist_min       = -1.0
normal_hist_max       = 1.0
normal_hist_bin_edges = linspace(normal_hist_min, normal_hist_max, normal_hist_n_bins+1)

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
color_hist_denorm_n_bins    = 20
color_hist_denorm_min       = 0.0
color_hist_denorm_max       = 2.0
color_hist_denorm_bin_edges = linspace(color_hist_denorm_min, color_hist_denorm_max, color_hist_denorm_n_bins+1)

# DIFFUSE REFLECTANCE
color_hist_norm_n_bins    = 10
color_hist_norm_min       = 0.0
color_hist_norm_max       = 1.0
color_hist_norm_bin_edges = linspace(color_hist_norm_min, color_hist_norm_max, color_hist_norm_n_bins+1)

# RGB COLOR
# DIFFUSE ILLUMINATION
# NON-DIFFUSE RESIDUAL
# DIFFUSE REFLECTANCE
hue_saturation_hist_n_bins    = 100
hue_saturation_hist_min       = -1
hue_saturation_hist_max       = 1
hue_saturation_hist_bin_edges = linspace(hue_saturation_hist_min, hue_saturation_hist_max, hue_saturation_hist_n_bins+1)

brightness_hist_linear_n_bins    = 1000
brightness_hist_linear_min       = 0.0
brightness_hist_linear_max       = 10.0
brightness_hist_linear_bin_edges = linspace(brightness_hist_linear_min, brightness_hist_linear_max, brightness_hist_linear_n_bins+1)

brightness_hist_log_n_bins    = 1000
brightness_hist_log_base      = 10.0
brightness_hist_log_min       = -3.0 # 0.001
brightness_hist_log_max       = 1.0  # 10.0
brightness_hist_log_bin_edges = logspace(brightness_hist_log_min, brightness_hist_log_max, brightness_hist_log_n_bins+1, base=brightness_hist_log_base)

# OBJECT VOLUME (LINEAR)
object_volume_hist_linear_n_bins    = 1000
object_volume_hist_linear_min       = 0.0
object_volume_hist_linear_max       = 1000.0
object_volume_hist_linear_bin_edges = linspace(object_volume_hist_linear_min, object_volume_hist_linear_max, object_volume_hist_linear_n_bins+1)

# OBJECT VOLUME (LOG)
object_volume_hist_log_n_bins    = 1000
object_volume_hist_log_base      = 10.0
object_volume_hist_log_min       = -6.0 # 0.000001
object_volume_hist_log_max       = 3.0  # 1000.0
object_volume_hist_log_bin_edges = logspace(object_volume_hist_log_min, object_volume_hist_log_max, object_volume_hist_log_n_bins+1, base=object_volume_hist_log_base)



metadata_camera_trajectories_csv_file = os.path.join(args.analysis_dir, "metadata_camera_trajectories.csv")

# rename_axis() sets the name of the current index
# reset_index() demotes the existing index to a column and creates a new unnamed index
# set_index() sets the current index
df_camera_trajectories = pd.read_csv(metadata_camera_trajectories_csv_file).rename_axis("camera_trajectory_id").reset_index().set_index("Animation")

batch_dir = os.path.join(args.analysis_dir, "image_statistics", args.batch_name)

unique_objects_per_image_hist_hdf5_file               = os.path.join(batch_dir, "metadata_unique_objects_per_image_hist.hdf5")
unique_classes_per_image_hist_hdf5_file               = os.path.join(batch_dir, "metadata_unique_classes_per_image_hist.hdf5")
unique_objects_per_class_hist_hdf5_file               = os.path.join(batch_dir, "metadata_unique_objects_per_class_hist.hdf5")
pixels_per_class_hist_hdf5_file                       = os.path.join(batch_dir, "metadata_pixels_per_class_hist.hdf5")
depth_hist_linear_hdf5_file                           = os.path.join(batch_dir, "metadata_depth_hist_linear.hdf5")
depth_hist_log_hdf5_file                              = os.path.join(batch_dir, "metadata_depth_hist_log.hdf5")
normal_hist_hdf5_file                                 = os.path.join(batch_dir, "metadata_normal_hist.hdf5")
rgb_color_hist_hdf5_file                              = os.path.join(batch_dir, "metadata_rgb_color_hist.hdf5")
rgb_color_hue_saturation_hist_hdf5_file               = os.path.join(batch_dir, "metadata_rgb_color_hue_saturation_hist.hdf5")
rgb_color_brightness_hist_linear_hdf5_file            = os.path.join(batch_dir, "metadata_rgb_color_brightness_hist_linear.hdf5")
rgb_color_brightness_hist_log_hdf5_file               = os.path.join(batch_dir, "metadata_rgb_color_brightness_hist_log.hdf5")
diffuse_illumination_hist_hdf5_file                   = os.path.join(batch_dir, "metadata_diffuse_illumination_hist.hdf5")
diffuse_illumination_hue_saturation_hist_hdf5_file    = os.path.join(batch_dir, "metadata_diffuse_illumination_hue_saturation_hist.hdf5")
diffuse_illumination_brightness_hist_linear_hdf5_file = os.path.join(batch_dir, "metadata_diffuse_illumination_brightness_hist_linear.hdf5")
diffuse_illumination_brightness_hist_log_hdf5_file    = os.path.join(batch_dir, "metadata_diffuse_illumination_brightness_hist_log.hdf5")
diffuse_reflectance_hist_hdf5_file                    = os.path.join(batch_dir, "metadata_diffuse_reflectance_hist.hdf5")
diffuse_reflectance_hue_saturation_hist_hdf5_file     = os.path.join(batch_dir, "metadata_diffuse_reflectance_hue_saturation_hist.hdf5")
diffuse_reflectance_brightness_hist_linear_hdf5_file  = os.path.join(batch_dir, "metadata_diffuse_reflectance_brightness_hist_linear.hdf5")
diffuse_reflectance_brightness_hist_log_hdf5_file     = os.path.join(batch_dir, "metadata_diffuse_reflectance_brightness_hist_log.hdf5")
residual_hist_hdf5_file                               = os.path.join(batch_dir, "metadata_residual_hist.hdf5")
residual_hue_saturation_hist_hdf5_file                = os.path.join(batch_dir, "metadata_residual_hue_saturation_hist.hdf5")
residual_brightness_hist_linear_hdf5_file             = os.path.join(batch_dir, "metadata_residual_brightness_hist_linear.hdf5")
residual_brightness_hist_log_hdf5_file                = os.path.join(batch_dir, "metadata_residual_brightness_hist_log.hdf5")
object_volume_hist_linear_hdf5_file                   = os.path.join(batch_dir, "metadata_object_volume_hist_linear.hdf5")
object_volume_hist_log_hdf5_file                      = os.path.join(batch_dir, "metadata_object_volume_hist_log.hdf5")

if args.load_snapshot:
    print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Loading histograms from snapshot...")
    with h5py.File(unique_objects_per_image_hist_hdf5_file,               "r") as f: unique_objects_per_image_hist               = f["dataset"][:].astype(int64)
    with h5py.File(unique_classes_per_image_hist_hdf5_file,               "r") as f: unique_classes_per_image_hist               = f["dataset"][:].astype(int64)
    with h5py.File(unique_objects_per_class_hist_hdf5_file,               "r") as f: unique_objects_per_class_hist               = f["dataset"][:].astype(int64)
    with h5py.File(pixels_per_class_hist_hdf5_file,                       "r") as f: pixels_per_class_hist                       = f["dataset"][:].astype(int64)
    with h5py.File(depth_hist_linear_hdf5_file,                           "r") as f: depth_hist_linear                           = f["dataset"][:].astype(int64)
    with h5py.File(depth_hist_log_hdf5_file,                              "r") as f: depth_hist_log                              = f["dataset"][:].astype(int64)
    with h5py.File(normal_hist_hdf5_file,                                 "r") as f: normal_hist                                 = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_hist_hdf5_file,                              "r") as f: rgb_color_hist                              = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_hue_saturation_hist_hdf5_file,               "r") as f: rgb_color_hue_saturation_hist               = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_brightness_hist_linear_hdf5_file,            "r") as f: rgb_color_brightness_hist_linear            = f["dataset"][:].astype(int64)
    with h5py.File(rgb_color_brightness_hist_log_hdf5_file,               "r") as f: rgb_color_brightness_hist_log               = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hist_hdf5_file,                   "r") as f: diffuse_illumination_hist                   = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_hue_saturation_hist_hdf5_file,    "r") as f: diffuse_illumination_hue_saturation_hist    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_brightness_hist_linear_hdf5_file, "r") as f: diffuse_illumination_brightness_hist_linear = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_illumination_brightness_hist_log_hdf5_file,    "r") as f: diffuse_illumination_brightness_hist_log    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hist_hdf5_file,                    "r") as f: diffuse_reflectance_hist                    = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_hue_saturation_hist_hdf5_file,     "r") as f: diffuse_reflectance_hue_saturation_hist     = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_brightness_hist_linear_hdf5_file,  "r") as f: diffuse_reflectance_brightness_hist_linear  = f["dataset"][:].astype(int64)
    with h5py.File(diffuse_reflectance_brightness_hist_log_hdf5_file,     "r") as f: diffuse_reflectance_brightness_hist_log     = f["dataset"][:].astype(int64)
    with h5py.File(residual_hist_hdf5_file,                               "r") as f: residual_hist                               = f["dataset"][:].astype(int64)
    with h5py.File(residual_hue_saturation_hist_hdf5_file,                "r") as f: residual_hue_saturation_hist                = f["dataset"][:].astype(int64)
    with h5py.File(residual_brightness_hist_linear_hdf5_file,             "r") as f: residual_brightness_hist_linear             = f["dataset"][:].astype(int64)
    with h5py.File(residual_brightness_hist_log_hdf5_file,                "r") as f: residual_brightness_hist_log                = f["dataset"][:].astype(int64)
    with h5py.File(object_volume_hist_linear_hdf5_file,                   "r") as f: object_volume_hist_linear                   = f["dataset"][:].astype(int64)
    with h5py.File(object_volume_hist_log_hdf5_file,                      "r") as f: object_volume_hist_log                      = f["dataset"][:].astype(int64)

else:
    print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Initializing histograms...")
    unique_objects_per_image_hist               = zeros(unique_objects_per_image_hist_n_bins, dtype=int64)
    unique_classes_per_image_hist               = zeros(unique_classes_per_image_hist_n_bins, dtype=int64)
    unique_objects_per_class_hist               = zeros(per_class_hist_n_bins,                dtype=int64)
    pixels_per_class_hist                       = zeros(per_class_hist_n_bins,                dtype=int64)
    depth_hist_linear                           = zeros(depth_hist_linear_n_bins,             dtype=int64)
    depth_hist_log                              = zeros(depth_hist_log_n_bins,                dtype=int64)
    normal_hist                                 = zeros((normal_hist_n_bins, normal_hist_n_bins), dtype=int64)
    rgb_color_hist                              = zeros((color_hist_denorm_n_bins, color_hist_denorm_n_bins, color_hist_denorm_n_bins), dtype=int64)
    rgb_color_hue_saturation_hist               = zeros((hue_saturation_hist_n_bins, hue_saturation_hist_n_bins), dtype=int64)
    rgb_color_brightness_hist_linear            = zeros(brightness_hist_linear_n_bins,        dtype=int64)
    rgb_color_brightness_hist_log               = zeros(brightness_hist_log_n_bins,           dtype=int64)
    diffuse_illumination_hist                   = zeros((color_hist_denorm_n_bins, color_hist_denorm_n_bins, color_hist_denorm_n_bins), dtype=int64)
    diffuse_illumination_hue_saturation_hist    = zeros((hue_saturation_hist_n_bins, hue_saturation_hist_n_bins), dtype=int64)
    diffuse_illumination_brightness_hist_linear = zeros(brightness_hist_linear_n_bins,        dtype=int64)
    diffuse_illumination_brightness_hist_log    = zeros(brightness_hist_log_n_bins,           dtype=int64)
    residual_hist                               = zeros((color_hist_denorm_n_bins, color_hist_denorm_n_bins, color_hist_denorm_n_bins), dtype=int64)
    residual_hue_saturation_hist                = zeros((hue_saturation_hist_n_bins, hue_saturation_hist_n_bins), dtype=int64)
    residual_brightness_hist_linear             = zeros(brightness_hist_linear_n_bins,        dtype=int64)
    residual_brightness_hist_log                = zeros(brightness_hist_log_n_bins,           dtype=int64)
    diffuse_reflectance_hist                    = zeros((color_hist_norm_n_bins, color_hist_norm_n_bins, color_hist_norm_n_bins), dtype=int64)
    diffuse_reflectance_hue_saturation_hist     = zeros((hue_saturation_hist_n_bins, hue_saturation_hist_n_bins), dtype=int64)
    diffuse_reflectance_brightness_hist_linear  = zeros(brightness_hist_linear_n_bins,        dtype=int64)
    diffuse_reflectance_brightness_hist_log     = zeros(brightness_hist_log_n_bins,           dtype=int64)
    object_volume_hist_linear                   = zeros(object_volume_hist_linear_n_bins,     dtype=int64)
    object_volume_hist_log                      = zeros(object_volume_hist_log_n_bins,        dtype=int64)



def process_scene(s, args):

    global unique_objects_per_image_hist
    global unique_classes_per_image_hist
    global unique_objects_per_class_hist
    global pixels_per_class_hist
    global depth_hist_linear
    global depth_hist_log
    global normal_hist
    global rgb_color_hist
    global rgb_color_hue_saturation_hist
    global rgb_color_brightness_hist_linear
    global rgb_color_brightness_hist_log
    global diffuse_illumination_hist
    global diffuse_illumination_hue_saturation_hist
    global diffuse_illumination_brightness_hist_linear
    global diffuse_illumination_brightness_hist_log
    global residual_hist
    global residual_hue_saturation_hist
    global residual_brightness_hist_linear
    global residual_brightness_hist_log
    global diffuse_reflectance_hist
    global diffuse_reflectance_hue_saturation_hist
    global diffuse_reflectance_brightness_hist_linear
    global diffuse_reflectance_brightness_hist_log
    global object_volume_hist_linear
    global object_volume_hist_log

    scene_name = s["name"]

    scene_dir  = os.path.join(dataset_scenes_dir, scene_name)    
    detail_dir = os.path.join(scene_dir, "_detail")
    mesh_dir   = os.path.join(scene_dir, "_detail", "mesh")
    images_dir = os.path.join(dataset_scenes_dir, scene_name, "images")

    metadata_scene_file = os.path.join(detail_dir, "metadata_scene.csv")
    df_scene = pd.read_csv(metadata_scene_file, index_col="parameter_name")
    meters_per_asset_unit = df_scene.loc["meters_per_asset_unit"][0]

    metadata_cameras_csv_file = os.path.join(detail_dir, "metadata_cameras.csv")
    df_cameras = pd.read_csv(metadata_cameras_csv_file)
    cameras = df_cameras.to_records()



    # check if scene has been flagged for exclusion
    scene_included_in_dataset = False
    for c in cameras:
        camera_trajectory_name = scene_name + "_" + c["camera_name"]
        scene_type = df_camera_trajectories.loc[camera_trajectory_name]["Scene type"]
        if scene_type != "OUTSIDE VIEWING AREA (BAD INITIALIZATION)" and scene_type != "OUTSIDE VIEWING AREA (BAD TRAJECTORY)":
            scene_included_in_dataset = True
            break
    if not scene_included_in_dataset:
        print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] No good camera trajectories for scene " + scene_name + ", skipping...")
        return



    print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Generating image statistics for scene " + scene_name + "...")

    # UNIQUE OBJECTS PER CLASS: Compute the semantic label for each object in the scene.
    # If there is any ambiguity about the label, just ignore the object. Could replace
    # with a majority vote.
    mesh_objects_si_hdf5_file  = os.path.join(mesh_dir, "mesh_objects_si.hdf5")
    mesh_objects_sii_hdf5_file = os.path.join(mesh_dir, "mesh_objects_sii.hdf5")

    if args.bounding_box_type == "axis_aligned":
        metadata_semantic_instance_bounding_box_extents_hdf5_file = os.path.join(mesh_dir, "metadata_semantic_instance_bounding_box_axis_aligned_extents.hdf5")
    if args.bounding_box_type == "object_aligned_2d":
        metadata_semantic_instance_bounding_box_extents_hdf5_file = os.path.join(mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_2d_extents.hdf5")
    if args.bounding_box_type == "object_aligned_3d":
        metadata_semantic_instance_bounding_box_extents_hdf5_file = os.path.join(mesh_dir, "metadata_semantic_instance_bounding_box_object_aligned_3d_extents.hdf5")

    with h5py.File(mesh_objects_si_hdf5_file,                                 "r") as f: mesh_objects_si      = f["dataset"][:]
    with h5py.File(mesh_objects_sii_hdf5_file,                                "r") as f: mesh_objects_sii     = f["dataset"][:]
    with h5py.File(metadata_semantic_instance_bounding_box_extents_hdf5_file, "r") as f: bounding_box_extents = f["dataset"][:]

    mesh_objects_sii_unique               = unique(mesh_objects_sii)
    mesh_objects_sii_unique_non_null_only = mesh_objects_sii_unique[mesh_objects_sii_unique != -1]
    num_mesh_objects_sii_unique           = mesh_objects_sii_unique_non_null_only.shape[0]

    mesh_objects_sii_to_si_map = {}

    for i in range(num_mesh_objects_sii_unique):

        sii                     = mesh_objects_sii_unique_non_null_only[i]
        si_unique               = unique(mesh_objects_si[mesh_objects_sii == sii])
        si_unique_non_null_only = si_unique[si_unique != -1]
        num_si_unique           = si_unique_non_null_only.shape[0]

        if num_si_unique == 0:
            print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: SEMANTIC INSTANCE ID " + str(sii) + " HAS NO SEMANTIC ID...")
            mesh_objects_sii_to_si_map[sii] = -1
        if num_si_unique == 1:
            mesh_objects_sii_to_si_map[sii] = si_unique_non_null_only[0]
        if num_si_unique > 1:
            semantic_names = [ semantic_id_to_name_map[si] for si in si_unique_non_null_only ]
            print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: SEMANTIC INSTANCE ID " + str(sii) + " HAS MORE THAN ONE SEMANTIC ID (" + str(si_unique) + ", " + str(semantic_names) + ")...")
            mesh_objects_sii_to_si_map[sii] = -1



    # iterate over the camera trajectories in the scene
    if args.camera_names is not None:
        cameras = [ c for c in df_cameras.to_records() if fnmatch.fnmatch(c["camera_name"], args.camera_names) ]
    else:
        cameras = df_cameras.to_records()

    unique_semantic_instance_ids_current_scene = array([])

    for c in cameras:

        camera_name = c["camera_name"]

        # check if camera trajectory is flagged for exclusion
        camera_trajectory_name = scene_name + "_" + camera_name
        scene_type = df_camera_trajectories.loc[camera_trajectory_name]["Scene type"]
        if scene_type == "OUTSIDE VIEWING AREA (BAD INITIALIZATION)" or scene_type == "OUTSIDE VIEWING AREA (BAD TRAJECTORY)":
            print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Camera " + camera_name + " is outside the viewing area, skipping...")
            continue

        print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] For scene " + scene_name + ", generating image statistics for camera " + camera_name + "...")

        in_scene_fileroot        = "scene"
        in_final_hdf5_dir        = os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_final_hdf5")
        in_geometry_hdf5_dir     = os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry_hdf5")
        in_camera_trajectory_dir = os.path.join(detail_dir, camera_name)

        camera_keyframe_frame_indices_hdf5_file = os.path.join(in_camera_trajectory_dir, "camera_keyframe_frame_indices.hdf5")
        camera_keyframe_positions_hdf5_file     = os.path.join(in_camera_trajectory_dir, "camera_keyframe_positions.hdf5")

        with h5py.File(camera_keyframe_frame_indices_hdf5_file, "r") as f: camera_keyframe_frame_indices = f["dataset"][:]
        with h5py.File(camera_keyframe_positions_hdf5_file,     "r") as f: camera_keyframe_positions     = f["dataset"][:]

        assert all(camera_keyframe_frame_indices == arange(camera_keyframe_frame_indices.shape[0]))

        num_camera_positions = camera_keyframe_frame_indices.shape[0]

        for i in range(num_camera_positions):

            camera_position = camera_keyframe_positions[i]

            in_file_root = "frame.%04d" % i

            in_depth_meters_hdf5_file      = os.path.join(in_geometry_hdf5_dir, in_file_root + ".depth_meters.hdf5")
            in_normal_cam_hdf5_file        = os.path.join(in_geometry_hdf5_dir, in_file_root + ".normal_cam.hdf5")
            in_normal_world_hdf5_file      = os.path.join(in_geometry_hdf5_dir, in_file_root + ".normal_world.hdf5")
            in_position_hdf5_file          = os.path.join(in_geometry_hdf5_dir, in_file_root + ".position.hdf5")
            in_render_entity_id_hdf5_file  = os.path.join(in_geometry_hdf5_dir, in_file_root + ".render_entity_id.hdf5")
            in_semantic_hdf5_file          = os.path.join(in_geometry_hdf5_dir, in_file_root + ".semantic.hdf5")
            in_semantic_instance_hdf5_file = os.path.join(in_geometry_hdf5_dir, in_file_root + ".semantic_instance.hdf5")

            in_rgb_hdf5_file                  = os.path.join(in_final_hdf5_dir, in_file_root + ".color.hdf5")
            in_diffuse_illumination_hdf5_file = os.path.join(in_final_hdf5_dir, in_file_root + ".diffuse_illumination.hdf5")
            in_diffuse_reflectance_hdf5_file  = os.path.join(in_final_hdf5_dir, in_file_root + ".diffuse_reflectance.hdf5")
            in_residual_hdf5_file             = os.path.join(in_final_hdf5_dir, in_file_root + ".residual.hdf5")

            try:
                with h5py.File(in_depth_meters_hdf5_file,      "r") as f: depth_meters      = f["dataset"][:].astype(float32)
                with h5py.File(in_normal_cam_hdf5_file,        "r") as f: normal_cam        = f["dataset"][:].astype(float32)
                with h5py.File(in_normal_world_hdf5_file,      "r") as f: normal_world      = f["dataset"][:].astype(float32)
                with h5py.File(in_position_hdf5_file,          "r") as f: position          = f["dataset"][:].astype(float32)
                with h5py.File(in_render_entity_id_hdf5_file,  "r") as f: render_entity_id  = f["dataset"][:].astype(int32)
                with h5py.File(in_semantic_hdf5_file,          "r") as f: semantic          = f["dataset"][:].astype(int32)
                with h5py.File(in_semantic_instance_hdf5_file, "r") as f: semantic_instance = f["dataset"][:].astype(int32)

                with h5py.File(in_rgb_hdf5_file,                  "r") as f: rgb_color            = f["dataset"][:].astype(float32)
                with h5py.File(in_diffuse_illumination_hdf5_file, "r") as f: diffuse_illumination = f["dataset"][:].astype(float32)
                with h5py.File(in_diffuse_reflectance_hdf5_file,  "r") as f: diffuse_reflectance  = f["dataset"][:].astype(float32)
                with h5py.File(in_residual_hdf5_file,             "r") as f: residual             = f["dataset"][:].astype(float32)
            except:
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: COULD NOT LOAD IMAGE DATA: " + in_file_root + "...")
                continue

            assert all(semantic != 0)
            assert all(semantic_instance != 0)

            #
            # Compute a valid mask, where valid means:
            # 1. There was some valid geometry rendered at that pixel. AND
            # 2. There are no inf values in any of the floating-point buffers at that pixel.
            # We need to handle this case explicitly because we save our data as float16, so
            # some data that might not have been rendered as inf originally will become inf when
            # we save our HDF5 data. AND
            # 3. Has a non-zero normal at that pixel.
            # We need to handle this case explicitly because V-Ray might render geometry with
            # zero normals.
            #
            
            valid_mask = render_entity_id != -1
            valid_mask_ = valid_mask.copy()

            infinite_vals_mask = logical_not(isfinite(depth_meters)) 
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_depth_meters_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(normal_cam), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_normal_cam_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(normal_world), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_normal_world_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(position), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_position_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(rgb_color), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_rgb_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(diffuse_illumination), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_diffuse_illumination_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(diffuse_reflectance), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_diffuse_reflectance_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            infinite_vals_mask = logical_not(all(isfinite(residual), axis=2))
            if any(logical_and(valid_mask, infinite_vals_mask)):
                warning_pixels_mask = logical_and(valid_mask, infinite_vals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NON-FINITE VALUE AT VALID PIXEL IN " + in_residual_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[infinite_vals_mask] = False

            zero_normals_mask = all(isclose(normal_cam, 0.0), axis=2)
            if any(logical_and(valid_mask, zero_normals_mask)):
                warning_pixels_mask = logical_and(valid_mask, zero_normals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: ZERO NORMALS AT VALID PIXEL IN " + in_normal_cam_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[zero_normals_mask] = False

            zero_normals_mask = all(isclose(normal_world, 0.0), axis=2)
            if any(logical_and(valid_mask, zero_normals_mask)):
                warning_pixels_mask = logical_and(valid_mask, zero_normals_mask)
                warning_pixels_y, warning_pixels_x = where(warning_pixels_mask)
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: ZERO NORMALS AT VALID PIXEL IN " + in_normal_world_hdf5_file + " (num_pixels=" + str(warning_pixels_y.shape[0]) + "; see pixel y=" + str(warning_pixels_y[0]) + ", x=" + str(warning_pixels_x[0]) + ")")
            valid_mask_[zero_normals_mask] = False

            valid_mask   = valid_mask_
            invalid_mask = logical_not(valid_mask)

            valid_mask_1d   = valid_mask.reshape(-1)
            invalid_mask_1d = invalid_mask.reshape(-1)

            if not any(valid_mask_1d):
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: NO VALID PIXELS, SKIPPING...")
                continue

            # make sure normals are correctly normalized - should do this when generating the HDF5 data?
            normal_cam_1d_ = normal_cam.reshape(-1,3)
            normal_cam_1d_[invalid_mask_1d] = -987654321.0
            normal_cam_1d_ = sklearn.preprocessing.normalize(normal_cam_1d_)
            normal_cam     = normal_cam_1d_.reshape(normal_cam.shape)

            normal_world_1d_ = normal_world.reshape(-1,3)
            normal_world_1d_[invalid_mask_1d] = -987654321.0
            normal_world_1d_ = sklearn.preprocessing.normalize(normal_world_1d_)
            normal_world     = normal_world_1d_.reshape(normal_world.shape)

            # compute flat lists of valid values
            depth_meters_1d      = depth_meters.reshape(-1)[valid_mask_1d]
            normal_cam_1d        = normal_cam.reshape(-1,3)[valid_mask_1d]
            normal_world_1d      = normal_world.reshape(-1,3)[valid_mask_1d]
            position_1d          = position.reshape(-1,3)[valid_mask_1d]
            semantic_1d          = semantic.reshape(-1)[valid_mask_1d]
            semantic_instance_1d = semantic_instance.reshape(-1)[valid_mask_1d]

            rgb_color_1d            = rgb_color.reshape(-1,3)[valid_mask_1d]
            diffuse_illumination_1d = diffuse_illumination.reshape(-1,3)[valid_mask_1d]
            diffuse_reflectance_1d  = diffuse_reflectance.reshape(-1,3)[valid_mask_1d]
            residual_1d             = residual.reshape(-1,3)[valid_mask_1d]

            assert allclose(linalg.norm(normal_cam_1d,   axis=1), 1.0)
            assert allclose(linalg.norm(normal_world_1d, axis=1), 1.0)

            if (any(diffuse_reflectance_1d < 0.0)):
                outliers = sort(diffuse_reflectance_1d[diffuse_reflectance_1d < 0.0])
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: OUTLIER DIFFUSE REFLECTANCE DATA: " + str(outliers.shape[0]) + " outliers, min outlier = " + str(outliers[0]) + ", max outlier = " + str(outliers[-1]))
            if (any(diffuse_reflectance_1d > 1.0)):
                outliers = sort(diffuse_reflectance_1d[diffuse_reflectance_1d > 1.0])
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: OUTLIER DIFFUSE REFLECTANCE DATA: " + str(outliers.shape[0]) + " outliers, min outlier = " + str(outliers[0]) + ", max outlier = " + str(outliers[-1]))

            # orient normals towards the camera - should do this when generating the HDF5 data?
            position_1d_     = position.reshape(-1,3)
            normal_world_1d_ = normal_world.reshape(-1,3)

            position_1d_[invalid_mask_1d]     = -987654321.0
            normal_world_1d_[invalid_mask_1d] = -987654321.0

            assert all(isfinite(position_1d_))

            surface_to_cam_world_normalized_1d_ = sklearn.preprocessing.normalize(camera_position - position_1d_)
            n_dot_v_1d_                         = sum(normal_world_1d_*surface_to_cam_world_normalized_1d_, axis=1)
            normal_back_facing_mask_1d_         = logical_and(valid_mask_1d, n_dot_v_1d_ < 0)
            normal_back_facing_mask             = normal_back_facing_mask_1d_.reshape(normal_world.shape[0], normal_world.shape[1])
            normal_back_facing_mask_1d          = normal_back_facing_mask_1d_.reshape(-1)

            normal_cam_ = normal_cam.copy()
            normal_cam_[normal_back_facing_mask] = -normal_cam_[normal_back_facing_mask]
            normal_cam_1d                        = normal_cam_.reshape(-1,3)[valid_mask_1d]

            assert allclose(linalg.norm(normal_cam_1d, axis=1), 1.0)

            # UNIQUE OBJECTS PER IMAGE: get number of unique objects in the current image (not including -1), increment histogram bin
            semantic_instance_1d_non_null_only = semantic_instance_1d[semantic_instance_1d != -1]
            num_unique_objects_current_image = unique(semantic_instance_1d_non_null_only).shape[0]

            if num_unique_objects_current_image < unique_objects_per_image_hist_n_bins:
                unique_objects_per_image_hist[num_unique_objects_current_image] += 1
            else:
                print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] WARNING: IMAGE " + in_file_root + " CONTAINS " + num_unique_objects_current_image + " UNIQUE OBJECTS, BUT HISTOGRAM ONLY HAS " + unique_objects_per_image_hist_n_bins + " BINS...")

            # UNIQUE CLASSES PER IMAGE: get number of unique classes (not including -1) in the current image, increment histogram bin
            semantic_1d_non_null_only = semantic_1d[semantic_1d != -1]
            num_unique_classes_current_image = unique(semantic_1d_non_null_only).shape[0]
            assert num_unique_classes_current_image < unique_classes_per_image_hist_n_bins
            unique_classes_per_image_hist[num_unique_classes_current_image] += 1

            # UNIQUE OBJECTS PER CLASS: update list of unique semantic instance ids (including -1) visible in the current scene
            if unique_semantic_instance_ids_current_scene.shape[0] == 0:
                unique_semantic_instance_ids_current_scene = unique(semantic_instance_1d)
            else:
                unique_semantic_instance_ids_current_scene = unique(r_[ unique_semantic_instance_ids_current_scene, semantic_instance_1d ])

            # PIXELS PER CLASS: compute histogram (including -1) for current image
            H, H_edges = histogram(semantic_1d, bins=per_class_hist_n_bins, range=(per_class_hist_min_bin_center - 0.5, per_class_hist_max_bin_center + 0.5))
            pixels_per_class_hist += H

            # DEPTH (LINEAR)
            H, H_edges = histogram(depth_meters_1d, bins=depth_hist_linear_bin_edges)
            depth_hist_linear += H

            # DEPTH (LOG)
            H, H_edges = histogram(depth_meters_1d, bins=depth_hist_log_bin_edges)
            depth_hist_log += H

            # NORMAL
            H, H_edges = histogramdd(normal_cam_1d[:,[1,0]], bins=normal_hist_n_bins, range=[(normal_hist_min, normal_hist_max), (normal_hist_min, normal_hist_max)])
            normal_hist += H.astype(int64)

            #
            # compute brightness according to "CCIR601 YIQ" method, use CGIntrinsics strategy for tonemapping but exclude gamma, see [1,2]
            # [1] https://github.com/snavely/pbrs_tonemapper/blob/master/tonemap_rgbe.py
            # [2] https://landofinterruptions.co.uk/manyshades
            #

            def rgb_to_brightness(vals_1d_rgb):
                return 0.3*vals_1d_rgb[:,0] + 0.59*vals_1d_rgb[:,1] + 0.11*vals_1d_rgb[:,2]

            def rgb_to_hsv_xyz(vals_1d_rgb):
                vals_1d_hsv     = matplotlib.colors.rgb_to_hsv(vals_1d_rgb)
                vals_1d_h       = vals_1d_hsv[:,0]
                vals_1d_s       = vals_1d_hsv[:,1]
                vals_1d_v       = vals_1d_hsv[:,2]
                vals_1d_theta   = vals_1d_h*2*pi
                vals_1d_hsv_x   = vals_1d_s*cos(vals_1d_theta)
                vals_1d_hsv_y   = vals_1d_s*sin(vals_1d_theta)
                vals_1d_hsv_z   = vals_1d_v
                vals_1d_hsv_xyz = c_[vals_1d_hsv_x, vals_1d_hsv_y, vals_1d_hsv_z]
                return vals_1d_hsv_xyz

            # compute linearly tonemapped values
            percentile                        = 90
            brightness_nth_percentile_desired = 0.8

            if count_nonzero(valid_mask) == 0:
                scale = 1.0
            else:
                brightness_1d = rgb_to_brightness(rgb_color_1d)

                eps                               = 0.0001
                brightness_nth_percentile_current = np.percentile(brightness_1d, percentile)

                if brightness_nth_percentile_current < eps:
                    scale = 0.0
                else:
                    scale = brightness_nth_percentile_desired / brightness_nth_percentile_current

            rgb_color_1d_tm            = scale*rgb_color_1d
            diffuse_illumination_1d_tm = scale*diffuse_illumination_1d
            residual_1d_tm             = scale*residual_1d

            # compute normalized hue saturation values
            rgb_color_1d_norm            = sklearn.preprocessing.normalize(rgb_color_1d)
            diffuse_illumination_1d_norm = sklearn.preprocessing.normalize(diffuse_illumination_1d)
            diffuse_reflectance_1d_norm  = sklearn.preprocessing.normalize(diffuse_reflectance_1d)
            residual_1d_norm             = sklearn.preprocessing.normalize(residual_1d)

            rgb_color_1d_norm_hsv_xyz            = rgb_to_hsv_xyz(rgb_color_1d_norm)
            diffuse_illumination_1d_norm_hsv_xyz = rgb_to_hsv_xyz(diffuse_illumination_1d_norm)
            diffuse_reflectance_1d_norm_hsv_xyz  = rgb_to_hsv_xyz(diffuse_reflectance_1d_norm)
            residual_1d_norm_hsv_xyz             = rgb_to_hsv_xyz(residual_1d_norm)

            # commpute brightness values
            rgb_color_1d_brightness            = rgb_to_brightness(rgb_color_1d)
            diffuse_illumination_1d_brightness = rgb_to_brightness(diffuse_illumination_1d)
            diffuse_reflectance_1d_brightness  = rgb_to_brightness(diffuse_reflectance_1d)
            residual_1d_brightness             = rgb_to_brightness(residual_1d)

            # RGB COLOR
            H, H_edges = histogramdd(rgb_color_1d_tm[:,[2,1,0]], bins=color_hist_denorm_n_bins, range=[(color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max)])
            rgb_color_hist += H.astype(int64)
            H, H_edges = histogramdd(rgb_color_1d_norm_hsv_xyz[:,[1,0]], bins=hue_saturation_hist_n_bins, range=[(hue_saturation_hist_min, hue_saturation_hist_max), (hue_saturation_hist_min, hue_saturation_hist_max)])
            rgb_color_hue_saturation_hist += H.astype(int64)
            H, H_edges = histogram(rgb_color_1d_brightness, bins=brightness_hist_linear_bin_edges)
            rgb_color_brightness_hist_linear += H
            H, H_edges = histogram(rgb_color_1d_brightness, bins=brightness_hist_log_bin_edges)
            rgb_color_brightness_hist_log += H

            # DIFFUSE ILLUMINATION
            H, H_edges = histogramdd(diffuse_illumination_1d_tm[:,[2,1,0]], bins=color_hist_denorm_n_bins, range=[(color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max)])
            diffuse_illumination_hist += H.astype(int64)
            H, H_edges = histogramdd(diffuse_illumination_1d_norm_hsv_xyz[:,[1,0]], bins=hue_saturation_hist_n_bins, range=[(hue_saturation_hist_min, hue_saturation_hist_max), (hue_saturation_hist_min, hue_saturation_hist_max)])
            diffuse_illumination_hue_saturation_hist += H.astype(int64)
            H, H_edges = histogram(diffuse_illumination_1d_brightness, bins=brightness_hist_linear_bin_edges)
            diffuse_illumination_brightness_hist_linear += H
            H, H_edges = histogram(diffuse_illumination_1d_brightness, bins=brightness_hist_log_bin_edges)
            diffuse_illumination_brightness_hist_log += H

            # DIFFUSE REFLECTANCE
            H, H_edges = histogramdd(diffuse_reflectance_1d[:,[2,1,0]], bins=color_hist_norm_n_bins, range=[(color_hist_norm_min, color_hist_norm_max), (color_hist_norm_min, color_hist_norm_max), (color_hist_norm_min, color_hist_norm_max)])
            diffuse_reflectance_hist += H.astype(int64)
            H, H_edges = histogramdd(diffuse_reflectance_1d_norm_hsv_xyz[:,[1,0]], bins=hue_saturation_hist_n_bins, range=[(hue_saturation_hist_min, hue_saturation_hist_max), (hue_saturation_hist_min, hue_saturation_hist_max)])
            diffuse_reflectance_hue_saturation_hist += H.astype(int64)
            H, H_edges = histogram(diffuse_reflectance_1d_brightness, bins=brightness_hist_linear_bin_edges)
            diffuse_reflectance_brightness_hist_linear += H
            H, H_edges = histogram(diffuse_reflectance_1d_brightness, bins=brightness_hist_log_bin_edges)
            diffuse_reflectance_brightness_hist_log += H

            # NON-DIFFUSE RESIDUAL
            H, H_edges = histogramdd(residual_1d_tm[:,[2,1,0]], bins=color_hist_denorm_n_bins, range=[(color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max), (color_hist_denorm_min, color_hist_denorm_max)])
            residual_hist += H.astype(int64)
            H, H_edges = histogramdd(residual_1d_norm_hsv_xyz[:,[1,0]], bins=hue_saturation_hist_n_bins, range=[(hue_saturation_hist_min, hue_saturation_hist_max), (hue_saturation_hist_min, hue_saturation_hist_max)])
            residual_hue_saturation_hist += H.astype(int64)
            H, H_edges = histogram(residual_1d_brightness, bins=brightness_hist_linear_bin_edges)
            residual_brightness_hist_linear += H
            H, H_edges = histogram(residual_1d_brightness, bins=brightness_hist_log_bin_edges)
            residual_brightness_hist_log += H

            print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Processing frame " + str(i) + " (scale=" + str(scale) + ")...")

            # import mayavi.mlab
            # path_utils.add_path_to_sys_path("../lib", mode="relative_to_cwd", frame=inspect.currentframe())
            # import mayavi_utils

            # color_hist_bin_centers_x_1d = color_hist_bin_edges[:-1] + diff(color_hist_bin_edges)/2.0
            # color_hist_bin_centers_y_1d = color_hist_bin_edges[:-1] + diff(color_hist_bin_edges)/2.0
            # color_hist_bin_centers_z_1d = color_hist_bin_edges[:-1] + diff(color_hist_bin_edges)/2.0

            # color_hist_bin_centers_z, color_hist_bin_centers_y, color_hist_bin_centers_x = meshgrid(color_hist_bin_centers_x_1d, color_hist_bin_centers_y_1d, color_hist_bin_centers_z_1d, indexing="ij")
            # color_hist_bin_centers_1d = c_[ color_hist_bin_centers_x.ravel(), color_hist_bin_centers_y.ravel(), color_hist_bin_centers_z.ravel() ]

            # in_geometry_preview_dir = os.path.join(images_dir, in_scene_fileroot + "_" + camera_name + "_geometry_preview")

            # # SEMANTIC
            # semantic_img_file = os.path.join(in_geometry_preview_dir, in_file_root + ".semantic.png")
            # semantic_img      = imread(semantic_img_file)
            # semantic_img_1d   = semantic_img.reshape(-1,4)[:,0:3]

            # H, H_edges = histogramdd(semantic_img_1d[:,[2,1,0]], bins=color_hist_n_bins, range=[(0,1), (0,1), (0,1)])
            # H_norm    = H / H.sum()
            # H_norm_1d = H_norm.ravel()
            # mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
            # mayavi_utils.points3d_color_by_rgb_value(color_hist_bin_centers_1d, colors=color_hist_bin_centers_1d, sizes=H_norm_1d, scale_factor=0.5)
            # mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
            # mayavi.mlab.axes()
            # mayavi.mlab.xlabel("R")
            # mayavi.mlab.ylabel("G")
            # mayavi.mlab.zlabel("B")
            # mayavi.mlab.show()

            # # SEMANTIC INSTANCE
            # semantic_instance_img_file = os.path.join(in_geometry_preview_dir, in_file_root + ".semantic_instance.png")
            # semantic_instance_img      = imread(semantic_instance_img_file)
            # semantic_instance_img_1d   = semantic_instance_img.reshape(-1,4)[:,0:3]

            # H, H_edges = histogramdd(semantic_instance_img_1d[:,[2,1,0]], bins=color_hist_n_bins, range=[(0,1), (0,1), (0,1)])
            # H_norm    = H / H.sum()
            # H_norm_1d = H_norm.ravel()
            # mayavi.mlab.figure(bgcolor=(1,1,1), fgcolor=(0,0,0), engine=None, size=(512, 512))
            # mayavi_utils.points3d_color_by_rgb_value(color_hist_bin_centers_1d, colors=color_hist_bin_centers_1d, sizes=H_norm_1d, scale_factor=0.5)
            # mayavi.mlab.outline(color=(0,0,0), extent=[0,1,0,1,0,1])
            # mayavi.mlab.axes()
            # mayavi.mlab.xlabel("R")
            # mayavi.mlab.ylabel("G")
            # mayavi.mlab.zlabel("B")
            # mayavi.mlab.show()

    # OBJECT VOLUME (LINEAR)
    # OBJECT VOLUME (LOG)
    # UNIQUE OBJECTS PER CLASS
    unique_semantic_instance_ids_current_scene_non_null_only = unique_semantic_instance_ids_current_scene[unique_semantic_instance_ids_current_scene != -1]

    if unique_semantic_instance_ids_current_scene_non_null_only.shape[0] > 0:

        # OBJECT VOLUME (LINEAR)
        # OBJECT VOLUME (LOG)
        bounding_box_extents_meters       = meters_per_asset_unit*bounding_box_extents
        bounding_box_volumes_meters_cubed = prod(bounding_box_extents_meters[unique_semantic_instance_ids_current_scene_non_null_only], axis=1)

        # OBJECT VOLUME (LINEAR)
        H, H_edges = histogram(bounding_box_volumes_meters_cubed, bins=object_volume_hist_linear_bin_edges)
        object_volume_hist_linear += H

        # OBJECT VOLUME (LOG)
        H, H_edges = histogram(bounding_box_volumes_meters_cubed, bins=object_volume_hist_log_bin_edges)
        object_volume_hist_log += H

        # UNIQUE OBJECTS PER CLASS: compute histogram (including -1) for current scene
        semantic_ids_current_scene = [ mesh_objects_sii_to_si_map[sii] for sii in unique_semantic_instance_ids_current_scene_non_null_only ]

        H, H_edges = histogram(semantic_ids_current_scene, bins=per_class_hist_n_bins, range=(per_class_hist_min_bin_center - 0.5, per_class_hist_max_bin_center + 0.5))
        unique_objects_per_class_hist += H



    print("[HYPERSIM: DATASET_GENERATE_IMAGE_STATISTICS] Saving snapshot...")

    if not os.path.exists(batch_dir): os.makedirs(batch_dir)

    with h5py.File(unique_objects_per_image_hist_hdf5_file,               "w") as f: f.create_dataset("dataset", data=unique_objects_per_image_hist)
    with h5py.File(unique_classes_per_image_hist_hdf5_file,               "w") as f: f.create_dataset("dataset", data=unique_classes_per_image_hist)
    with h5py.File(unique_objects_per_class_hist_hdf5_file,               "w") as f: f.create_dataset("dataset", data=unique_objects_per_class_hist)
    with h5py.File(pixels_per_class_hist_hdf5_file,                       "w") as f: f.create_dataset("dataset", data=pixels_per_class_hist)
    with h5py.File(depth_hist_linear_hdf5_file,                           "w") as f: f.create_dataset("dataset", data=depth_hist_linear)
    with h5py.File(depth_hist_log_hdf5_file,                              "w") as f: f.create_dataset("dataset", data=depth_hist_log)
    with h5py.File(normal_hist_hdf5_file,                                 "w") as f: f.create_dataset("dataset", data=normal_hist)
    with h5py.File(rgb_color_hist_hdf5_file,                              "w") as f: f.create_dataset("dataset", data=rgb_color_hist)
    with h5py.File(rgb_color_hue_saturation_hist_hdf5_file,               "w") as f: f.create_dataset("dataset", data=rgb_color_hue_saturation_hist)
    with h5py.File(rgb_color_brightness_hist_linear_hdf5_file,            "w") as f: f.create_dataset("dataset", data=rgb_color_brightness_hist_linear)
    with h5py.File(rgb_color_brightness_hist_log_hdf5_file,               "w") as f: f.create_dataset("dataset", data=rgb_color_brightness_hist_log)
    with h5py.File(diffuse_illumination_hist_hdf5_file,                   "w") as f: f.create_dataset("dataset", data=diffuse_illumination_hist)
    with h5py.File(diffuse_illumination_hue_saturation_hist_hdf5_file,    "w") as f: f.create_dataset("dataset", data=diffuse_illumination_hue_saturation_hist)
    with h5py.File(diffuse_illumination_brightness_hist_linear_hdf5_file, "w") as f: f.create_dataset("dataset", data=diffuse_illumination_brightness_hist_linear)
    with h5py.File(diffuse_illumination_brightness_hist_log_hdf5_file,    "w") as f: f.create_dataset("dataset", data=diffuse_illumination_brightness_hist_log)
    with h5py.File(diffuse_reflectance_hist_hdf5_file,                    "w") as f: f.create_dataset("dataset", data=diffuse_reflectance_hist)
    with h5py.File(diffuse_reflectance_hue_saturation_hist_hdf5_file,     "w") as f: f.create_dataset("dataset", data=diffuse_reflectance_hue_saturation_hist)
    with h5py.File(diffuse_reflectance_brightness_hist_linear_hdf5_file,  "w") as f: f.create_dataset("dataset", data=diffuse_reflectance_brightness_hist_linear)
    with h5py.File(diffuse_reflectance_brightness_hist_log_hdf5_file,     "w") as f: f.create_dataset("dataset", data=diffuse_reflectance_brightness_hist_log)
    with h5py.File(residual_hist_hdf5_file,                               "w") as f: f.create_dataset("dataset", data=residual_hist)
    with h5py.File(residual_hue_saturation_hist_hdf5_file,                "w") as f: f.create_dataset("dataset", data=residual_hue_saturation_hist)
    with h5py.File(residual_brightness_hist_linear_hdf5_file,             "w") as f: f.create_dataset("dataset", data=residual_brightness_hist_linear)
    with h5py.File(residual_brightness_hist_log_hdf5_file,                "w") as f: f.create_dataset("dataset", data=residual_brightness_hist_log)
    with h5py.File(object_volume_hist_linear_hdf5_file,                   "w") as f: f.create_dataset("dataset", data=object_volume_hist_linear)
    with h5py.File(object_volume_hist_log_hdf5_file,                      "w") as f: f.create_dataset("dataset", data=object_volume_hist_log)



for s in scenes:
    process_scene(s, args)



print("[HYPERSIM: DATASET_GENERATE_IMAGES_STATISTICS] Finished.")
