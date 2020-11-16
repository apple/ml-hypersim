#
# For licensing see accompanying LICENSE.txt file.
# Copyright (C) 2020 Apple Inc. All Rights Reserved.
#

from pylab import *

import argparse
import h5py
import inspect
import os
import pandas as pd

import path_utils
path_utils.add_path_to_sys_path("../lib", mode="relative_to_current_source_dir", frame=inspect.currentframe())
import octomap_utils

parser = argparse.ArgumentParser()
parser.add_argument("--scene_dir", required=True)
args = parser.parse_args()

assert os.path.exists(args.scene_dir)

path_utils.add_path_to_sys_path(os.path.join(args.scene_dir, "..", ".."), mode="relative_to_cwd", frame=inspect.currentframe())
import _dataset_config



print("[HYPERSIM: SCENE_GENERATE_OCTOMAP] Begin...")



scene_name       = os.path.basename(args.scene_dir)
asset_export_dir = os.path.join(args.scene_dir, "_asset_export")
detail_dir       = os.path.join(args.scene_dir, "_detail")
tmp_dir          = os.path.join(args.scene_dir, "_tmp")
mesh_dir         = os.path.join(detail_dir, "mesh")

mesh_vertices_hdf5_file                = os.path.join(mesh_dir, "mesh_vertices.hdf5")
mesh_faces_vi_hdf5_file                = os.path.join(mesh_dir, "mesh_faces_vi.hdf5")
metadata_cameras_asset_export_csv_file = os.path.join(asset_export_dir, "metadata_cameras_asset_export.csv")
metadata_scene_csv_file                = os.path.join(detail_dir, "metadata_scene.csv")

out_dir = os.path.join(detail_dir, "octomap")

octomap_bt_file                  = os.path.join(out_dir, "octomap.bt")
octomap_free_space_min_hdf5_file = os.path.join(out_dir, "octomap_free_space_min.hdf5")
octomap_free_space_max_hdf5_file = os.path.join(out_dir, "octomap_free_space_max.hdf5")

if not os.path.exists(out_dir): os.makedirs(out_dir)



with h5py.File(mesh_vertices_hdf5_file, "r") as f: mesh_vertices = f["dataset"][:]
with h5py.File(mesh_faces_vi_hdf5_file, "r") as f: mesh_faces_vi = f["dataset"][:]



scene                 = [ s for s in _dataset_config.scenes if s["name"] == scene_name ][0]
df_scene              = pd.read_csv(metadata_scene_csv_file, index_col="parameter_name")
meters_per_asset_unit = df_scene.loc["meters_per_asset_unit"][0]
asset_units_per_meter = 1.0 / meters_per_asset_unit



# parameters for space carving algorithm

n_rays                  = 512*512 # shoot this many rays during each iteration of space carving, i.e., at each position
n_iters                 = 5       # perform this many iterations of space carving
n_voxel_size            = scene["voxel_extent_meters"]*asset_units_per_meter
n_octomap_size          = scene["scene_extent_meters"]*asset_units_per_meter

# When performing space carving, we may need to perturb our starting position so it is not in occupied space. When
# deciding on a perturbation direction, we would like to perturb the starting position towards wide open parts of
# the scene, e.g., away from walls and tightly enclosed spaces. So, we shoot rays in dense set of directions and try
# the directions with the greatest intersection distances first. However, this heursitic is susceptible to
# perturbing our starting position through tiny holes in nearby walls. To make our heuristic more robust, we perform
# a min-pooling operation for the intersection distances across neighboring rays, effectively dilating the angular
# extent of the scene geometry. This strategy prevents us from perturbing our starting position through small holes
# in the scene geometry. This parameter controls the neighborhood size for the min-pooling operation.
n_ray_nearest_neighbors = 50



# get cameras from the original asset file
df_cameras_asset_export = pd.read_csv(metadata_cameras_asset_export_csv_file)

start_camera_positions = None

for c in df_cameras_asset_export.to_records():

    camera_name = c["camera_name"]

    camera_dir                             = os.path.join(asset_export_dir, camera_name)
    camera_keyframe_positions_hdf5_file    = os.path.join(camera_dir, "camera_keyframe_positions.hdf5")
    camera_keyframe_orientations_hdf5_file = os.path.join(camera_dir, "camera_keyframe_orientations.hdf5")

    with h5py.File(camera_keyframe_positions_hdf5_file,    "r") as f: camera_keyframe_positions    = f["dataset"][:]
    with h5py.File(camera_keyframe_orientations_hdf5_file, "r") as f: camera_keyframe_orientations = f["dataset"][:]

    if start_camera_positions is None:
        start_camera_positions = camera_keyframe_positions
    else:
        start_camera_positions = r_[ start_camera_positions, camera_keyframe_positions ]

start_camera_positions = pd.DataFrame(data=start_camera_positions).drop_duplicates().to_numpy()

assert start_camera_positions.shape[0] > 0

min_start_camera_positions    = np.min(start_camera_positions, axis=0)
max_start_camera_positions    = np.max(start_camera_positions, axis=0)
start_camera_positions_extent = max_start_camera_positions - min_start_camera_positions

print("[HYPERSIM: SCENE_GENERATE_OCTOMAP] Extent of all cameras: " + str(start_camera_positions_extent))
print("[HYPERSIM: SCENE_GENERATE_OCTOMAP] Octomap extent: " + str(n_octomap_size))

assert all(start_camera_positions_extent <= n_octomap_size)

octomap_padding = n_octomap_size - start_camera_positions_extent
octomap_min     = min_start_camera_positions - (octomap_padding/2.0)
octomap_max     = max_start_camera_positions + (octomap_padding/2.0)



# generate octomap
free_space_min, free_space_max = \
    octomap_utils.generate_octomap(
        mesh_vertices,
        mesh_faces_vi,
        start_camera_positions,
        octomap_min,
        octomap_max,
        n_rays,
        n_iters,
        n_voxel_size,
        n_ray_nearest_neighbors,
        octomap_file=octomap_bt_file,
        tmp_dir=tmp_dir)

with h5py.File(octomap_free_space_min_hdf5_file, "w") as f: f.create_dataset("dataset", data=free_space_min)
with h5py.File(octomap_free_space_max_hdf5_file, "w") as f: f.create_dataset("dataset", data=free_space_max)



print("[HYPERSIM: SCENE_GENERATE_OCTOMAP] Finished.")
